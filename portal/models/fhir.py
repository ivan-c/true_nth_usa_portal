"""Model classes for retaining FHIR data"""
from datetime import date, datetime
import dateutil
from flask import current_app
import json
import pytz
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, ENUM
import requests

from ..extensions import db
from .lazy import lazyprop
from ..system_uri import TRUENTH_CLINICAL_CODE_SYSTEM, TRUENTH_VALUESET
from ..views.fhir import valueset_ascceg


def as_fhir(obj):
    """For builtin types needing FHIR formatting help

    Returns obj as JSON FHIR formatted string

    """
    if hasattr(obj, 'as_fhir'):
        return obj.as_fhir()
    if isinstance(obj, datetime):
        # Make SURE we only communicate unaware or UTC timezones
        tz = getattr(obj, 'tzinfo', None)
        if tz and tz != pytz.utc:
            current_app.logger.error("Datetime export of NON-UTC timezone")
        return obj.strftime("%Y-%m-%dT%H:%M:%S%z")
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')


class FHIR_datetime(object):
    """Utility class/namespace for working with FHIR datetimes"""

    @staticmethod
    def as_fhir(obj):
        return as_fhir(obj)

    @staticmethod
    def parse(data):
        """Parse input string to generate a UTC datetime instance"""
        dt = dateutil.parser.parse(data)
        if dt.tzinfo:
            # Convert to UTC if necessary
            if dt.tzinfo != pytz.utc:
                dt = dt.astimezone(pytz.utc)
        return dt

    @staticmethod
    def now():
        """Generates a FHIR compliant datetime string for current moment"""
        return datetime.utcnow().isoformat()+'Z'


class CodeableConceptCoding(db.Model):
    """Link table joining CodeableConcept with n Codings"""

    __tablename__ = 'codeable_concept_codings'
    id = db.Column(db.Integer, primary_key=True)
    codeable_concept_id = db.Column(db.ForeignKey(
        'codeable_concepts.id'), nullable=False)
    coding_id =  db.Column(db.ForeignKey('codings.id'), nullable=False)

    # Maintain a unique relationship between each codeable concepts
    # and the its of codings.  Therefore, a CodeableConcept always
    # contains the superset of all codings given for the concept.
    db.UniqueConstraint('codeable_concept_id', 'coding_id',
                        name='unique_codeable_concept_coding')


class CodeableConcept(db.Model):
    __tablename__ = 'codeable_concepts'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    codings = db.relationship("Coding", secondary='codeable_concept_codings')

    def __str__(self):
        """Print friendly format for logging, etc."""
        summary = "CodeableConcept {} [".format(
            self.text if self.text else '')
        summary += ','.join([str(coding) for coding in self.codings])
        return summary + ']'

    @classmethod
    def from_fhir(cls, data):
        cc = cls()
        if 'text' in data:
            cc.text = data['text']
        for coding in data['coding']:
            item = Coding.from_fhir(coding)
            cc.codings.append(item)
        return cc.add_if_not_found()

    def as_fhir(self):
        """Return self in JSON FHIR formatted string"""
        d = {"coding": [coding.as_fhir() for coding in self.codings]}
        if self.text:
            d['text'] = self.text
        return d

    def add_if_not_found(self, commit_immediately=False):
        """Add self to database, or return existing

        Queries for similar, matching on the set of contained
        codings alone.  Adds if no match is found.

        @return: the new or matched CodeableConcept

        """
        # we're imposing a constraint, where any CodeableConcept pointing
        # at a particular Coding will be the ONLY CodeableConcept for that
        # particular Coding.
        coding_ids = [c.id for c in self.codings]
        if not coding_ids:
            current_app.logger.error("no coding_ids found for {}".format(self))
        found = CodeableConceptCoding.query.filter(
            CodeableConceptCoding.coding_id.in_(coding_ids)).first()
        if not found:
            # First time for this (set) of codes, add new rows
            db.session.add(self)
            if commit_immediately:
                db.session.commit()
        else:
            # Build a union of all codings found, old and new
            old = CodeableConcept.query.get(found.codeable_concept_id)
            self.text = self.text if self.text else old.text
            self.codings = list(set(old.codings).union(set(self.codings)))
            self.id = found.codeable_concept_id
        self = db.session.merge(self)
        return self


class Coding(db.Model):
    __tablename__ = 'codings'
    id = db.Column(db.Integer, primary_key=True)
    system = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(80), nullable=False)
    display = db.Column(db.Text, nullable=False)
    __table_args__ = (UniqueConstraint('system', 'code',
        name='_system_code'),)

    def __str__(self):
        """Print friendly format for logging, etc."""
        return "Coding {0.code}, {0.display}, {0.system}".format(self)

    @classmethod
    def from_fhir(cls, data):
        """Factory method to lookup or create instance from fhir"""
        cc = cls()
        for i in ("system", "code", "display"):
            if i in data:
                cc.__setattr__(i, data[i])
        return cc.add_if_not_found()

    def as_fhir(self):
        """Return self in JSON FHIR formatted string"""
        d = {}
        for i in ("system", "code", "display"):
            if getattr(self, i):
                d[i] = getattr(self, i)
        return d

    def add_if_not_found(self):
        """Add self to database, or return existing

        Queries for similar, existing CodeableConcept (matches on
        system and code alone).  Populates self.id if found, adds
        to database first if not.

        """
        if self.id:
            return self

        match = self.query.filter_by(system=self.system,
                code=self.code).first()
        if not match:
            db.session.add(self)
        elif self is not match:
            self = db.session.merge(match)
        return self


""" TrueNTH Clinical Codes """
class ClinicalConstants(object):

    def __iter__(self):
        for attr in dir(self):
            if attr.startswith('_'):
                continue
            yield getattr(self, attr)

    @lazyprop
    def BIOPSY(self):
        coding = Coding.query.filter_by(
            system=TRUENTH_CLINICAL_CODE_SYSTEM, code='111').one()
        cc = CodeableConcept(codings=[coding,]).add_if_not_found(True)
        assert coding in cc.codings
        return cc

    @lazyprop
    def PCaDIAG(self):
        coding = Coding.query.filter_by(
            system=TRUENTH_CLINICAL_CODE_SYSTEM, code='121').one()
        cc = CodeableConcept(codings=[coding,]).add_if_not_found(True)
        assert coding in cc.codings
        return cc

    @lazyprop
    def PCaLocalized(self):
        coding = Coding.query.filter_by(
            system=TRUENTH_CLINICAL_CODE_SYSTEM, code='141').one()
        cc = CodeableConcept(codings=[coding,]).add_if_not_found(True)
        assert coding in cc.codings
        return cc

    @lazyprop
    def TX(self):
        coding = Coding.query.filter_by(
            system=TRUENTH_CLINICAL_CODE_SYSTEM, code='131').one()
        cc = CodeableConcept(codings=[coding,]).add_if_not_found(True)
        assert coding in cc.codings
        return cc

    @lazyprop
    def TRUE_VALUE(self):
        value_quantity = ValueQuantity(
            value='true', units='boolean').add_if_not_found(True)
        return value_quantity

    @lazyprop
    def FALSE_VALUE(self):
        value_quantity = ValueQuantity(
            value='false', units='boolean').add_if_not_found(True)
        return value_quantity

CC = ClinicalConstants()


class ValueQuantity(db.Model):
    __tablename__ = 'value_quantities'
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(80))
    units = db.Column(db.String(80))
    system = db.Column(db.String(255))
    code = db.Column(db.String(80))

    def __str__(self):
        """Print friendly format for logging, etc."""
        components = ','.join([str(x) for x in
                               (self.value, self.units, self.system,
                               self.code) if x is not None])
        return "ValueQuantity " + components

    def as_fhir(self):
        """Return self in JSON FHIR formatted string"""
        d = {}
        for i in ("value", "units", "system", "code"):
            if getattr(self, i):
                d[i] = getattr(self, i)
        return {"valueQuantity": d}

    def add_if_not_found(self, commit_immediately=False):
        """Add self to database, or return existing

        Queries for similar, existing ValueQuantity (matches on
        value, units and system alone).  Populates self.id if found,
        adds to database first if not.

        """
        if self.id:
            return self

        lookup_value = self.value and str(self.value) or None
        match = self.query.filter_by(value=lookup_value,
                units=self.units, system=self.system).first()
        if not match:
            db.session.add(self)
            if commit_immediately:
                db.session.commit()
        elif self is not match:
            self = db.session.merge(match)
        return self


class Observation(db.Model):
    __tablename__ = 'observations'
    id = db.Column(db.Integer, primary_key=True)
    issued = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(80))
    codeable_concept_id = db.Column(db.ForeignKey('codeable_concepts.id'),
                                   nullable=False)
    value_quantity_id = db.Column(db.ForeignKey('value_quantities.id'),
                                 nullable=False)
    audit_id = db.Column(db.ForeignKey('audit.id'), nullable=False)

    audit = db.relationship('Audit', cascade="save-update")
    codeable_concept = db.relationship(CodeableConcept, cascade="save-update")
    value_quantity = db.relationship(ValueQuantity)
    performers = db.relationship('Performer', lazy='dynamic',
                                 cascade="save-update",
                                 secondary="observation_performers",
                                 backref=db.backref('observations'))

    def __str__(self):
        """Print friendly format for logging, etc."""
        return "Observation {0.codeable_concept} {0.value_quantity} "\
                "at {0.issued} by {0.performers} with status {0.status} ".\
                format(self)

    def as_fhir(self):
        """Return self in JSON FHIR formatted string"""
        fhir = {"resourceType": "Observation"}
        if self.audit:
            fhir['meta'] = self.audit.as_fhir()
        if self.issued:
            fhir['issued'] = as_fhir(self.issued)
        if self.status:
            fhir['status'] = self.status
        fhir['code'] = self.codeable_concept.as_fhir()
        fhir.update(self.value_quantity.as_fhir())
        if self.performers:
            fhir['performer'] = [p.as_fhir() for p in self.performers]
        return fhir

    def add_if_not_found(self, commit_immediately=False):
        """Add self to database, or return existing

        Queries for matching, existing Observation.
        Populates self.id if found, adds to database first if not.

        """
        if self.id:
            return self
        match_dict = {'issued': self.issued,
                      'status': self.status}
        if self.codeable_concept_id:
            match_dict['codeable_concept_id'] = self.codeable_concept_id
        if self.value_quantity_id:
            match_dict['value_quantity_id'] = self.value_quantity_id

        match = self.query.filter_by(**match_dict).first()
        if not match:
            db.session.add(self)
            if commit_immediately:
                db.session.commit()
        elif self is not match:
            self = db.session.merge(match)
        return self


class UserObservation(db.Model):
    __tablename__ = 'user_observations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id', ondelete='CASCADE'),
                       nullable=False)
    observation_id = db.Column(db.ForeignKey('observations.id'),
                              nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'observation_id',
        name='_user_observation'),)

    def add_if_not_found(self):
        """Add self to database, or return existing

        Queries for matching, existing UserObservation.
        Populates self.id if found, adds to database first if not.

        """
        if self.id:
            return self

        match = self.query.filter_by(user_id=self.user_id,
                observation_id=self.observation_id).first()
        if not match:
            db.session.add(self)
        elif self is not match:
            self = db.session.merge(match)
        return self


class UserEthnicity(db.Model):
    __tablename__ = 'user_ethnicities'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    coding_id = db.Column(db.ForeignKey('codings.id'), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'coding_id',
        name='_ethnicity_user_coding'),)

class UserRace(db.Model):
    __tablename__ = 'user_races'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    coding_id = db.Column(db.ForeignKey('codings.id'), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'coding_id',
        name='_race_user_coding'),)

class QuestionnaireResponse(db.Model):

    def default_status(context):
        return context.current_parameters['document']['status']

    def default_authored(context):
        return FHIR_datetime.parse(
            context.current_parameters['document']['authored'])

    __tablename__ = 'questionnaire_responses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id'))
    document = db.Column(JSONB)

    # Fields derived from document content
    status = db.Column(
        ENUM(
            'in-progress',
            'completed',
            name='questionnaire_response_statuses'
        ),
        default=default_status
    )

    authored = db.Column(
        db.DateTime,
        default=default_authored
    )

    def __str__(self):
        """Print friendly format for logging, etc."""
        return "QuestionnaireResponse {0.id} for user {0.user_id} "\
                "{0.status} {0.authored}".format(self)


def parse_concepts(elements, system):
    "recursive function to build array of concepts from nested structure"
    ccs = []
    for element in elements:
        ccs.append(Coding(code=element['code'],
                          display=element['display'],
                          system=system))
        if 'concept' in element:
            ccs += parse_concepts(element['concept'], system)
    return ccs


def fetch_HL7_V3_Namespace(valueSet):
    """Pull and parse the published FHIR ethnicity namespace"""
    src_url = 'http://hl7.org/fhir/v3/{valueSet}/v3-{valueSet}.json'.format(
        valueSet=valueSet)
    response = requests.get(src_url)
    load = response.text
    data = json.loads(load)
    return parse_concepts(data['codeSystem']['concept'],
                          system='http://hl7.org/fhir/v3/{}'.format(valueSet))

def fetch_local_valueset(valueSet):
    """Pull and parse the named valueSet from our local definition"""
    response = valueset_ascceg()
    data = json.loads(response.data)
    return parse_concepts(data['codeSystem']['concept'],
                          system='{}/{}'.format(TRUENTH_VALUESET,valueSet))


def add_static_concepts(only_quick=False):
    """Seed database with default static concepts

    Idempotent - run anytime to push any new concepts into existing dbs

    :param only_quick: For unit tests needing quick loads, set true
        unless the test needs the slow to load race and ethnicity data.

    """
    BIOPSY = Coding(system=TRUENTH_CLINICAL_CODE_SYSTEM, code='111',
                             display='biopsy')
    PCaDIAG = Coding(system=TRUENTH_CLINICAL_CODE_SYSTEM, code='121',
                              display='PCa diagnosis')
    PCaLocalized = Coding(system=TRUENTH_CLINICAL_CODE_SYSTEM, code='141',
                              display='PCa localized diagnosis')
    TX = Coding(system=TRUENTH_CLINICAL_CODE_SYSTEM, code='131',
                         display='treatment begun')

    concepts = [BIOPSY, PCaDIAG, PCaLocalized, TX]
    concepts += fetch_local_valueset('ascceg')
    if not only_quick:
        concepts += fetch_HL7_V3_Namespace('Ethnicity')
        concepts += fetch_HL7_V3_Namespace('Race')
    for concept in concepts:
        if not Coding.query.filter_by(code=concept.code,
                                      system=concept.system).first():
            db.session.add(concept)

    for clinical_concepts in CC:
        if not clinical_concepts in db.session():
            db.session.add(clinical_concepts)
