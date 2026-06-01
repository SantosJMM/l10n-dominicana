# -*- coding: utf-8 -*-
# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.


def post_init_hook(env):
    # Backfill tax metadata for DO companies that already had the chart loaded
    # before this module was installed.
    companies = env["res.company"].search([("chart_template", "=", "do")])

    for company in companies:
        company._l10n_do_configure_dgii_tax_types()
