from flask import Blueprint, request, url_for, flash
from flask import render_template, redirect
from formencode import Invalid

from nomenklatura.core import db
from nomenklatura.util import request_content, response_format
from nomenklatura.util import jsonify, Pager
from nomenklatura import authz
from nomenklatura.exc import NotFound
from nomenklatura.views.dataset import view as view_dataset
from nomenklatura.views.common import handle_invalid
from nomenklatura.matching import match as match_op
from nomenklatura.model import Dataset, Value

section = Blueprint('value', __name__)

@section.route('/<dataset>/values', methods=['GET'])
def index(dataset):
    dataset = Dataset.find(dataset)
    format = response_format()
    if format == 'json':
        return jsonify(Value.all(dataset))
    return "Not implemented!"

@section.route('/<dataset>/values', methods=['POST'])
def create(dataset):
    dataset = Dataset.find(dataset)
    authz.require(authz.dataset_edit(dataset))
    data = request_content()
    try:
        value = Value.create(dataset, data, request.account)
        db.session.commit()
        return redirect(url_for('.view',
            dataset=dataset.name,
            value=value.id))
    except Invalid, inv:
        return handle_invalid(inv, view_dataset, data=data, 
                              args=[dataset.name])

@section.route('/<dataset>/values/<value>', methods=['GET'])
def view(dataset, value):
    dataset = Dataset.find(dataset)
    value = Value.find(dataset, value)
    format = response_format()
    if format == 'json':
        return jsonify(value)
    query = request.args.get('query', '').strip().lower()
    choices = match_op(value.value, dataset)
    choices = filter(lambda (c,v,s): v != value, choices)
    if len(query):
        choices = filter(lambda (c,v,s): query in v.value.lower(),
                         choices)
    pager = Pager(choices, '.view', dataset=dataset.name,
                  value=value.id, limit=10)
    return render_template('value/view.html', dataset=dataset,
                           value=value, values=pager, query=query)

@section.route('/<dataset>/value', methods=['GET'])
def view_by_value(dataset):
    dataset = Dataset.find(dataset)
    value = Value.by_value(dataset, request.args.get('value'))
    if value is None:
        raise NotFound("No such value: %s" % request.args.get('value'))
    return view(dataset.name, value.id)

@section.route('/<dataset>/values/<value>', methods=['POST'])
def update(dataset, value):
    dataset = Dataset.find(dataset)
    authz.require(authz.dataset_edit(dataset))
    value = Value.find(dataset, value)
    data = request_content()
    try:
        value.update(data, request.account)
        db.session.commit()
        flash("Updated %s" % value.value, 'success')
        return redirect(url_for('.view', dataset=dataset.name, value=value.id))
    except Invalid, inv:
        return handle_invalid(inv, view, data=data,
                              args=[dataset.name, value.id])

@section.route('/<dataset>/values/<value>/merge', methods=['POST'])
def merge(dataset, value):
    dataset = Dataset.find(dataset)
    authz.require(authz.dataset_edit(dataset))
    value = Value.find(dataset, value)
    data = request_content()
    try:
        target = value.merge_into(data, request.account)
        db.session.commit()
        flash("Merged %s" % value.value, 'success')
        return redirect(url_for('.view', dataset=dataset.name,
                        value=target.id))
    except Invalid, inv:
        print inv
        return handle_invalid(inv, view, data=data,
                              args=[dataset.name, value.id])

