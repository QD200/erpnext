import frappe


def execute():
	assets = get_details_of_draft_or_submitted_depreciable_assets()

	for asset in assets:
		finance_book_rows = get_details_of_asset_finance_books_rows(asset.name)

		for fb_row in finance_book_rows:
			asset_depr_schedule_doc = frappe.new_doc("Asset Depreciation Schedule")

			asset_depr_schedule_doc.asset = asset.name
			asset_depr_schedule_doc.finance_book = fb_row.finance_book
			asset_depr_schedule_doc.finance_book_id = fb_row.idx
			asset_depr_schedule_doc.opening_accumulated_depreciation = (
				asset.opening_accumulated_depreciation
			)
			asset_depr_schedule_doc.depreciation_method = fb_row.depreciation_method
			asset_depr_schedule_doc.total_number_of_depreciations = fb_row.total_number_of_depreciations
			asset_depr_schedule_doc.frequency_of_depreciation = fb_row.frequency_of_depreciation
			asset_depr_schedule_doc.rate_of_depreciation = fb_row.rate_of_depreciation
			asset_depr_schedule_doc.expected_value_after_useful_life = (
				fb_row.expected_value_after_useful_life
			)
			asset_depr_schedule_doc.status = "Draft"

			asset_depr_schedule_doc.insert()

			update_depreciation_schedules(asset.name, asset_depr_schedule_doc.name, fb_row.idx)

			if asset.docstatus == 1:
				asset_depr_schedule_doc.submit()


def get_details_of_draft_or_submitted_depreciable_assets():
	asset = frappe.qb.DocType("Asset")

	records = (
		frappe.qb.from_(asset)
		.select(asset.name, asset.opening_accumulated_depreciation, asset.docstatus)
		.where(asset.calculate_depreciation == 1)
		.where(asset.docstatus < 2)
	).run(as_dict=True)

	return records


def get_details_of_asset_finance_books_rows(asset_name):
	afb = frappe.qb.DocType("Asset Finance Book")

	records = (
		frappe.qb.from_(afb)
		.select(
			afb.finance_book,
			afb.idx,
			afb.depreciation_method,
			afb.total_number_of_depreciations,
			afb.frequency_of_depreciation,
			afb.rate_of_depreciation,
			afb.expected_value_after_useful_life,
		)
		.where((afb.parenttype == "Asset") & (afb.parent == asset_name))
	).run(as_dict=True)

	return records


def update_depreciation_schedules(asset_name, asset_depr_schedule_name, fb_row_idx):
	ds = frappe.qb.DocType("Depreciation Schedule")

	depr_schedules = (
		frappe.qb.from_(ds)
		.select(ds.name)
		.where((ds.parent == asset_name) & (ds.finance_book_id == str(fb_row_idx)))
	).run(as_dict=True)

	for idx, depr_schedule in enumerate(depr_schedules, start=1):
		(
			frappe.qb.update(ds)
			.set(ds.idx, idx)
			.set(ds.parent, asset_depr_schedule_name)
			.set(ds.parentfield, "depreciation_schedule")
			.set(ds.parenttype, "Asset Depreciation Schedule")
			.where(ds.parent == depr_schedule.name)
		).run()
