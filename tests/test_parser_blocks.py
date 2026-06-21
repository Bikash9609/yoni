"""Parametrized parser tests for all 17 Yoni block kinds."""

from pathlib import Path

import pytest

from yoni import parse_file
from yoni.ast.action import ActionAST
from yoni.ast.capability import CapabilityAST
from yoni.ast.constraint import ConstraintAST
from yoni.ast.deployment import DeploymentAST
from yoni.ast.domain import DomainAST
from yoni.ast.entity import EntityAST
from yoni.ast.error import ErrorAST
from yoni.ast.event import EventAST
from yoni.ast.intent import IntentAST
from yoni.ast.migration import MigrationAST
from yoni.ast.project import ProjectAST
from yoni.ast.query import QueryAST
from yoni.ast.rule import RuleAST
from yoni.ast.state import StateAST
from yoni.ast.test import TestAST
from yoni.ast.view import ViewAST
from yoni.ast.workflow import WorkflowAST

FIXTURES = Path(__file__).parent / "fixtures"

BLOCK_CASES = [
    ("entity_customer.yoni", EntityAST, "ENT_CUSTOMER_001"),
    ("intent_create_invoice.yoni", IntentAST, "INT_CREATE_INV_001"),
    ("rule_adult.yoni", RuleAST, "RULE_ADULT_001"),
    ("query_active_customers.yoni", QueryAST, "QUERY_ACTIVE_001"),
    ("state_invoice_status.yoni", StateAST, "STS_INVOICE_001"),
    ("event_invoice_paid.yoni", EventAST, "EVT_INVOICE_PAID_001"),
    ("action_send_email.yoni", ActionAST, "ACT_SEND_EMAIL_001"),
    ("workflow_onboarding.yoni", WorkflowAST, "WF_ONBOARD_001"),
    ("constraint_email_unique.yoni", ConstraintAST, "CNST_EMAIL_UNIQUE_001"),
    ("error_customer_not_found.yoni", ErrorAST, "ERR_CUST_NOT_FOUND_001"),
    ("test_create_invoice.yoni", TestAST, "TST_CREATE_INV_001"),
    ("capability_email.yoni", CapabilityAST, "CAP_EMAIL_001"),
    ("view_customer_list.yoni", ViewAST, "VIEW_CUST_LIST_001"),
    ("project_billing.yoni", ProjectAST, "PROJ_BILLING_001"),
    ("domain_customer.yoni", DomainAST, "DOM_CUSTOMER_001"),
    ("deployment_prod.yoni", DeploymentAST, "DEP_PROD_001"),
    ("migration_customer_v2.yoni", MigrationAST, "MIG_CUST_V2_001"),
]


@pytest.mark.parametrize(("fixture", "ast_type", "block_id"), BLOCK_CASES)
def test_parse_block_fixture(fixture: str, ast_type: type, block_id: str) -> None:
    result = parse_file(FIXTURES / fixture)
    assert result.ok, result.errors
    assert isinstance(result.ast, ast_type)
    assert result.ast.id == block_id


def test_intent_process_ops() -> None:
    result = parse_file(FIXTURES / "intent_create_invoice.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, IntentAST)
    assert len(result.ast.process) == 4
    assert result.ast.process[0].op == "new"
    assert result.ast.inputs[1].ref is not None


def test_intent_section_order_violation() -> None:
    source = """intent Bad

id: INT_BAD_001
desc:
  Bad order.

process:

input:
"""
    from yoni import parse_source

    result = parse_source(source)
    assert not result.ok
    assert any(error.code == "YONI1007" for error in result.errors)


def test_missing_id() -> None:
    source = """entity Customer

desc:
  No id.
"""
    from yoni import parse_source

    result = parse_source(source)
    assert not result.ok
    assert any(error.code == "YONI1003" for error in result.errors)


def test_syntax_error() -> None:
    source = "notablock Foo\nid: X\n"
    from yoni import parse_source

    result = parse_source(source)
    assert result.ast is None
    assert any(error.code == "YONI1001" for error in result.errors)
