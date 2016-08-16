# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask.templating import render_template
from ...main import main


@main.route('/guidance/how-to-answer-supplier-questions')
def how_to_answer_supplier_questions():
    return render_template('guidance/answering_questions.html')


@main.route('/guidance/how-to-shortlist-suppliers')
def how_to_shortlist_suppliers():
    return render_template('guidance/shortlisting_suppliers.html')


@main.route('/guidance/how-to-evaluate-suppliers')
def how_to_evaluate_suppliers():
    return render_template('guidance/evaluating_suppliers.html')


@main.route('/guidance/how-marketplace-evaluated')
def how_marketplace_evaluated():
    return render_template('guidance/evaluated.html')


@main.route('/guidance/how-to-award-contract')
def how_to_award_contract():
    return render_template('guidance/awarding_contract.html')
