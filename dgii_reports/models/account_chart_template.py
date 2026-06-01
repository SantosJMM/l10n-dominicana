from odoo import models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _post_load_data(self, template_code, company, template_data):
        result = super()._post_load_data(template_code, company, template_data)
        # Configure DO tax metadata when the Dominican chart is loaded on a company.
        if template_code == "do":
            company._l10n_do_configure_dgii_tax_types()
        return result
