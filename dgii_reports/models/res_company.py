from odoo import models, api


DOMINICAN_TAX_CONFIGS = (
    ("tax_18_sale", "itbis", False),
    ("tax_0_sale", "itbis", False),
    ("tax_18_of_10", "itbis", False),
    ("tax_tip_sale", "tip", False),
    ("ret_5_income_gov", "isr", "07"),
    ("tax_18_purch", "itbis", False),
    ("tax_0_purch", "itbis", False),
    ("tax_16_purch", "itbis", False),
    ("tax_9_purch", "itbis", False),
    ("tax_8_purch", "itbis", False),
    ("tax_tip_purch", "tip", False),
    ("tax_18_purch_serv", "itbis", False),
    ("tax_18_importation", "itbis", False),
    ("tax_18_10_total_mount", "itbis", False),
    ("tax_18_property_cost", "itbis", False),
    ("tax_18_serv_cost", "itbis", False),
    ("ret_100_tax_security", "ritbis", False),
    ("ret_100_tax_nonprofit", "ritbis", False),
    ("ret_100_tax_person", "ritbis", False),
    ("ret_30_tax_moral", "ritbis", False),
    ("ret_30_tax_freelance", "ritbis", False),
    ("ret_75_tax_nonformal", "ritbis", False),
    ("ret_10_income_person", "isr", "02"),
    ("ret_10_income_rent", "isr", "01"),
    ("ret_10_income_dividend", "isr", "03"),
    ("ret_2_income_person", "isr", "03"),
    ("ret_2_income_transfer", "isr", "03"),
    ("ret_27_income_remittance", "isr", "03"),
    ("tax_10_telco", "isc", False),
    ("tax_2_telco", "other", False),
    ("tax_0015_bank", "other", False),
)


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _l10n_do_configure_dgii_tax_types(self):
        tax_model = self.env["account.tax"]
        if "l10n_do_tax_type" not in tax_model._fields:
            return

        companies = self or self.search([("chart_template", "=", "do")])
        chart_template_model = self.env["account.chart.template"]

        for company in companies.filtered(lambda c: c.chart_template == "do"):
            chart_template = chart_template_model.with_company(company)
            for tax_xmlid, tax_type, retention_type in DOMINICAN_TAX_CONFIGS:
                tax = chart_template.ref(tax_xmlid, raise_if_not_found=False)
                if not tax:
                    continue
                values: dict[str, str | bool] = {"l10n_do_tax_type": tax_type}
                if "isr_retention_type" in tax_model._fields:
                    values["isr_retention_type"] = retention_type or False
                tax.write(values)
