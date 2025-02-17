# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, time_diff_in_hours
from frappe import _
class ProcessOrder(Document):

	# @frappe.whitelist()    
	# def jobTotal(self):
	# 	total=0.0
	# 	doc=frappe.db.get_list('Process Order',fields=["job_offer","job_order_qty"])
	# 	for d in doc:
	# 		if str(d.job_offer) == str(self.job_offer):
	# 				total=total+float(d.job_order_qty)
	# 	frappe.msgprint(" Job Order = " +self.job_offer+ "   "+"  & Total created Order On This Job =  "+str(total))

	# @frappe.whitelist()
	# def upend_opcost_table(self):
	# 	doc=frappe.db.get_list('Job Offer Process')
	# 	for d in doc:
	# 		doc1=frappe.get_doc('Job Offer Process',d.name)
	# 		if(self.job_offer==d.name):
	# 			for d1 in doc1.get("operation_cost"):
	# 				self.append("operation_cost",{
	# 						"operations":d1.operations,
	# 						"cost":d1.cost,
	# 						"is_check":'0'
	# 						}
	# 					)
		
	@frappe.whitelist()
	def get_process_details(self):
		doc=frappe.db.get_list('Job Offer Process')
		tot_qty = 0.0
		for d in doc:
			doc1=frappe.get_doc('Job Offer Process',d.name)
			if(self.job_offer==doc1.job_order_name):
				self.definition_material_qty = doc1.definition_material_qty
				for d1 in doc1.get("materials"):
					self.append("materials",{
							"item_name":d1.item_name,
							"item":d1.item,
							"quantity":d1.quantity,
							"rate":d1.rate,
							"yeild":d1.yeild,
							"amount":d1.amount,
							"uom":d1.uom
							}
						)
				for d2 in doc1.get("finished_products"):
					self.append("finished_products",{
							"item":d2.item,
							"item_name":d2.item_name,
							"quantity":d2.quantity,
							"rate":d2.rate,
							"yeild":d2.yeild,
							"amount":d2.amount,
							"uom":d2.uom,
							"batch_no":d2.batch_no,
							"warehouse":d2.warehouse
							}
						)
				for d3 in doc1.get("scrap"):
					self.append("scrap",{
							"item":d3.item,
							"item_name":d3.item_name,
							"quantity":d3.quantity,
							"rate":d3.rate,
							"yeild":d3.yeild,
							"amount":d3.amount,
							"uom":d3.uom,
							"batch_no":d3.batch_no,
							"warehouse":d3.warehouse
							}
						)
				for d4 in doc1.get("operation_cost"):
					self.append("operation_cost",{
							"operations":d4.operations,
							# "cost":d4.cost,
							"process_order_cost":d4.definition_cost,
							}
						)
     
		# # Set costing_method
		# self.costing_method = frappe.db.get_value("Process Definition", self.process_name, "costing_method")
		# # Set Child Tables
		# process = frappe.get_doc("Process Definition", self.process_name)
		# # if process:
		# # 	if process.materials:
		# # 		self.add_item_in_table(process.materials, "materials")
		# # 	if process.finished_products:
		# # 		self.add_item_in_table(process.finished_products, "finished_products")
		# # 	if process.scrap:
		# # 		self.add_item_in_table(process.scrap, "scrap")
	@frappe.whitelist()
	def qtyupdate(self):
		self.secondTrigger()
		self.secondTrigger()

	@frappe.whitelist()
	def secondTrigger(self):
		temp=''
		# mqty=0.0
		# fpq=0.0
		# scq=0.0
		tocq=0.0
		# mam=0.0
		# fpam=0.0
		# scam=0.0
		tbam=0.0
  
		for m in self.get('materials'):
			temp=m.quantity
			if m.quantity > 0:
				m.quantity=(self.quantity * m.yeild) / 100
			tbam=float(m.quantity)*float(m.rate)
			m.amount=tbam
			self.materials_qty = sum(m.quantity for m in self.get("materials"))
			self.materials_amount = sum(m.amount for m in self.get("materials"))
		for toc in self.get('operation_cost'):
			# if(toc.is_check == 0):
				# toc.cost=(float(self.quantity)*float(self.definition_material_qty))
			# toc.cost=((float(toc.process_order_cost)/float(self.definition_material_qty)) * float(self.quantity))
			if(float(toc.process_order_cost)> 0 and float(self.definition_material_qty) >0 and float(self.quantity) > 0):
				toc.cost=((float(toc.process_order_cost)/float(self.definition_material_qty)) * float(self.quantity))
					# toc.is_check  = '1'
				# toc.cost = (toc.cost / self.definition_material_qty ) * self.quantity
				tocq=float(tocq)+float(toc.cost)
				self.total_operation_cost = sum(toc.cost for toc in self.get("operation_cost"))
   
		for fp in self.get('finished_products'):
			if fp.quantity >0 and temp >0:
				fp.quantity=str((int(fp.quantity)*int(self.quantity))/int(temp))
				fp.quantity = (fp.yeild / 100) * self.materials_qty
			tbam=float(fp.quantity)*float(fp.rate)
			fp.amount=tbam
			# fpam=float(fpam)+float(fp.amount)
			# fpq=float(fpq)+float(fp.quantity)
			pricelst = frappe.get_value("Manufacturing Rate Chart",{'process_type':self.process_type,"item_code":fp.item},"rate")
			fp.manufacturing_rate = pricelst
			if fp.manufacturing_rate == None:
				fp.manufacturing_rate = 0
			if fp.quantity == None:
				fp.quantity = 0
			fp.sale_value = fp.quantity * fp.manufacturing_rate
			self.total_sale_value = sum(fp.sale_value for fp in self.get("finished_products"))
			self.finished_products_qty = sum(fp.quantity for fp in self.get("finished_products"))
			self.finished_products_amount = sum(fp.amount for fp in self.get("finished_products"))
			for sc in self.get('scrap'):
				pricelst = frappe.get_value("Manufacturing Rate Chart",{'process_type':self.process_type,"item_code":sc.item},"rate")
				if(pricelst):
					sc.manufacturing_rate = pricelst
				else:
					sc.manufacturing_rate = 0
				sc.sale_value = float(sc.quantity) * float(sc.manufacturing_rate)
				self.scrap_qty = sum(sc.quantity for sc in self.get("scrap"))
				self.scrap_amount = sum(sc.amount for sc in self.get("scrap"))
				self.total_scrap_sale_value = sum(sc.sale_value for sc in self.get("scrap"))
			if fp.sale_value >0:
				fp.basic_value = (fp.sale_value / (self.total_sale_value +self.total_scrap_sale_value)) * (self.materials_amount)
			# fp.basic_value = (fp.sale_value / (self.total_sale_value +self.total_scrap_sale_value)) * (self.materials_amount + self.total_operation_cost)
			if fp.basic_value >0:
				fp.rate = fp.basic_value / fp.quantity
			fp.amount = fp.rate * fp.quantity
  
		for sc in self.get('scrap'):
			if int(temp):
				sc.quantity=str((int(sc.quantity)*int(self.quantity))/int(temp))
				sc.quantity = (sc.yeild / 100) * self.materials_qty
				tbam=float(sc.quantity)*float(sc.rate)
				sc.amount=tbam
			# scam=float(scam)+float(sc.amount)
			# scq=float(scq)+float(sc.quantity)
			# pricelst = frappe.get_value("Manufacturing Rate Chart",{'process_type':self.process_type,"item_code":sc.item},"rate")
			# sc.manufacturing_rate = pricelst
			# sc.sale_value = sc.quantity * sc.manufacturing_rate
			# self.total_scrap_sale_value = sum(sc.sale_value for sc in self.get("scrap"))
			# sc.basic_value = (sc.sale_value / (self.total_sale_value +self.total_scrap_sale_value)) * (self.materials_amount + self.total_operation_cost)
			if sc.sale_value >0:
				sc.basic_value = (sc.sale_value / (self.total_sale_value +self.total_scrap_sale_value)) * (self.materials_amount)
			sc.rate = sc.basic_value / sc.quantity
			sc.amount = sc.rate * sc.quantity

		
		# self.scrap_qty=scq
		# self.scrap_amount=scam

		self.all_finish_qty=self.finished_products_qty+self.scrap_qty
		self.total_all_amount=self.finished_products_amount+self.scrap_amount

		
  
		# for toc in self.get('operation_cost'):
		# 	toc.cost=str((int(toc.cost)*int(self.quantity))/int(temp))
		# 	tocq=float(tocq)+float(toc.cost)
		
		self.total_operation_cost=tocq
		self.diff_qty=float(self.all_finish_qty)-float(self.materials_qty)
		self.diff_amt=float(self.materials_amount+self.total_operation_cost)-float(self.total_all_amount)

		for ok in self.get('finished_products'):
			if ok.amount >0:
				ok.operation_cost = ( ok.amount / self.total_all_amount ) * self.total_operation_cost
			ok.total_cost = ok.amount + ok.operation_cost
			if ok.total_cost>0:
				ok.valuation_rate = ok.total_cost / ok.quantity
		for yes in self.get('scrap'):
			if yes.amount >0:
				yes.operation_cost = ( yes.amount / self.total_all_amount ) * self.total_operation_cost
			yes.total_cost = yes.amount + yes.operation_cost
			if yes.total_cost>0:
				yes.valuation_rate = yes.total_cost / yes.quantity
		# temp=0.0
		# tbam=0.0
  
		# for m in self.get('materials'):
		# 	temp=m.quantity
		# 	if m.quantity > 0:
		# 		m.quantity=(self.quantity * m.yeild) / 100
		# 	tbam=float(m.quantity)*float(m.rate)
		# 	m.amount=tbam
		# 	self.materials_qty = sum(m.quantity for m in self.get("materials"))
		# 	self.materials_amount = sum(m.amount for m in self.get("materials"))
		# for toc in self.get('operation_cost'):
		# 	if(toc.is_check == 0):
		# 		toc.cost=(float(toc.cost)*float(self.definition_material_qty))
		# 		toc.is_check  = '1'
		# 	# toc.cost = (toc.cost / self.definition_material_qty ) * self.quantity
		# 	tocq=float(tocq)+float(toc.cost)
		# 	self.total_operation_cost = sum(toc.cost for toc in self.get("operation_cost"))
   
		# for fp in self.get('finished_products'):
		# 	fp.quantity=(float(fp.quantity)*float(self.quantity))/float(temp)
		# 	fp.quantity = (fp.yeild / 100) * self.materials_qty
		# 	tbam=float(fp.quantity)*float(fp.rate)
		# 	fp.amount=tbam
		# 	pricelst = frappe.get_value("Manufacturing Rate Chart",{'process_type':self.process_type,"item_code":fp.item},"rate")
		# 	fp.manufacturing_rate = pricelst
		# 	if fp.manufacturing_rate == None:
		# 		fp.manufacturing_rate = 0
		# 	if fp.quantity == None:
		# 		fp.quantity = 0
		# 	fp.sale_value = fp.quantity * fp.manufacturing_rate
		# 	self.total_sale_value = sum(fp.sale_value for fp in self.get("finished_products"))
		# 	self.finished_products_qty = sum(fp.quantity for fp in self.get("finished_products"))
		# 	self.finished_products_amount = sum(fp.amount for fp in self.get("finished_products"))
		# 	for sc in self.get('scrap'):
		# 		pricelst = frappe.get_value("Manufacturing Rate Chart",{'process_type':self.process_type,"item_code":sc.item},"rate")
		# 		if(pricelst):
		# 			sc.manufacturing_rate = pricelst
		# 		else:
		# 			sc.manufacturing_rate = 0
		# 		sc.quantity=(float(sc.quantity)*float(self.quantity))/float(temp)
		# 		sc.quantity = (sc.yeild / 100) * self.materials_qty
		# 		tbam=float(sc.quantity)*float(sc.rate)
		# 		sc.amount=tbam
		# 		sc.sale_value = float(sc.quantity) * float(sc.manufacturing_rate)
		# 		self.scrap_qty = sum(sc.quantity for sc in self.get("scrap"))
		# 		self.scrap_amount = sum(sc.amount for sc in self.get("scrap"))
		# 		self.total_scrap_sale_value = sum(sc.sale_value for sc in self.get("scrap"))
		# 		sc.basic_value = (sc.sale_value / (self.total_sale_value +self.total_scrap_sale_value)) * (self.materials_amount)
		# 		sc.rate = sc.basic_value / sc.quantity
		# 		sc.amount = sc.rate * sc.quantity
		# 	for toc in self.get('operation_cost'):
		# 		toc.cost=(float(toc.cost)*int(self.quantity))/float(temp)
		# 		self.total_operation_cost = sum(toc.cost for toc in self.get("operation_cost"))
		# 	fp.basic_value = (fp.sale_value / (self.total_sale_value +self.total_scrap_sale_value)) * (self.materials_amount)
		# 	fp.rate = fp.basic_value / fp.quantity
		# 	fp.amount = fp.rate * fp.quantity
		# self.all_finish_qty=self.finished_products_qty+self.scrap_qty
		# self.total_all_amount=self.finished_products_amount+self.scrap_amount		
		# self.diff_qty=float(self.all_finish_qty)-float(self.materials_qty)
		# self.diff_amt=float(self.materials_amount+self.total_operation_cost)-float(self.total_all_amount)

		# for ok in self.get('finished_products'):
		# 	ok.operation_cost = ( ok.amount / self.total_all_amount ) * self.total_operation_cost
		# 	ok.total_cost = ok.amount + ok.operation_cost
		# 	ok.valuation_rate = ok.total_cost / ok.quantity
		# for yes in self.get('scrap'):
		# 	yes.operation_cost = ( yes.amount / self.total_all_amount ) * self.total_operation_cost
		# 	yes.total_cost = yes.amount + yes.operation_cost
		# 	yes.valuation_rate = yes.total_cost / yes.quantity

	@frappe.whitelist()
	def Get_Purchase_Rate(self,item,index):
		# ratevar = frappe.get_value("Bin", {"item_code": item, "warehouse": self.src_warehouse, "actual_qty": (">", 0)}, "valuation_rate")
		# if(ratevar):
		# 	self.get("materials")[index-1].rate=ratevar
		for fp in self.get('finished_products'):
			pricelst = frappe.get_value("Manufacturing Rate Chart",{'process_type':self.process_type,"item_code":fp.item},"rate")
			fp.manufacturing_rate = pricelst
		for sc in self.get('scrap'):
				pricelst = frappe.get_value("Manufacturing Rate Chart",{'process_type':self.process_type,"item_code":sc.item},"rate")
				sc.manufacturing_rate = pricelst

   
    
	@frappe.whitelist()
	def on_submit(self):
		
  
		if not self.wip_warehouse:
			frappe.throw(_("Work-in-Progress Warehouse is required before Submit"))
		if not self.fg_warehouse:
			frappe.throw(_("Target Warehouse is required before Submit"))
		if self.scrap and not self.scrap_warehouse:
			frappe.throw(_("Scrap Warehouse is required before submit"))

		frappe.db.set(self, 'status', 'Submitted')
  
		data = frappe.db.sql("""
								SELECT SUM(quantity) quantity
								FROM `tabProcess Order`
								WHERE job_offer=%s and docstatus = 1
							""",(self.job_offer),as_dict="True")

		tota_soso = (data[0]['quantity']) if (data[0]['quantity'])	 else 0
		src_wh,name= frappe.db.get_value("Job Offer Process", {'name':self.job_offer},["quantity","name"])
		if tota_soso == src_wh:
			frappe.db.set_value("Job Offer Process",name,'status',"Completed")
		else:
			pass
		if tota_soso > src_wh:
			frappe.throw("Your Batch Qty = "+str(tota_soso) +"is more than Process Qty ="+str(src_wh))
			
			




	@frappe.whitelist()
	def on_cancel(self):
		stock_entry = frappe.db.sql("""select name from `tabStock Entry`
			where process_order = %s and docstatus = 1""", self.name)
		if stock_entry:
			frappe.throw(_("Cannot cancel because submitted Stock Entry \
			{0} exists").format(stock_entry[0][0]))
		frappe.db.set(self, 'status', 'Cancelled')

   
	

	@frappe.whitelist()			
	def start_finish_processing(self, status):
		if status == "In Process":
			if not self.end_dt:
				self.end_dt = get_datetime()

		self.flags.ignore_validate_update_after_submit = True
		self.save()

		return self.make_stock_entry(status)
	@frappe.whitelist()
	def set_se_items_start(self, se):
		# set source and target warehouse
		se.from_warehouse = self.src_warehouse
		se.to_warehouse = self.wip_warehouse

		for item in self.materials:
			if self.src_warehouse:
				src_wh = self.src_warehouse
			else:
				src_wh = frappe.db.get_value("Item Default", {'parent': item.item, 'company': self.company}),
				src_wh = frappe.db.get_value("Item Default", {'parent': item.item, 'company': self.company},
											 ["default_warehouse"])
			# create stock entry lines
			se = self.set_se_items(se, item, src_wh, self.wip_warehouse, False)
		return se
		
	@frappe.whitelist()
	def set_se_items_finish(self, se):
		# set from and to warehouse
		se.from_warehouse = self.wip_warehouse
		se.to_warehouse = self.fg_warehouse
		se_materials = frappe.get_doc("Stock Entry", {"process_order": self.name, "docstatus": '1'})
		# get items to consume from previous stock entry or append to items
		# TODO allow multiple raw material transfer
		raw_material_cost = 0
		operating_cost = 0
		if se_materials:
			raw_material_cost = se_materials.total_incoming_value
			se.items = se_materials.items
			for item in se.items:
				item.s_warehouse = se.from_warehouse
				item.t_warehouse = None
		else:
			for item in self.materials:
				se = self.set_se_items(se, item, se.from_warehouse, None, False)
		# TODO calc raw_material_cost
		# no timesheet entries, calculate operating cost based on workstation hourly rate and process start, end
		hourly_rate = frappe.db.get_value("Workstation", self.workstation, "hour_rate")
		if hourly_rate:
			if self.operation_hours >= 0:
				hours = self.operation_hours
			else:
				hours = time_diff_in_hours(self.end_dt, self.start_dt)
				frappe.db.set(self, 'operation_hours', hours)
			operating_cost = hours * float(hourly_rate)
		production_cost = raw_material_cost + operating_cost
		# calc total_qty and total_sale_value
		qty_of_total_production = 0
		total_sale_value = 0
		for item in self.finished_products:
			if item.quantity >= 0:
				qty_of_total_production = float(qty_of_total_production) + item.quantity
				if self.costing_method == "Relative Sales Value":
					sale_value_of_pdt = frappe.db.get_value("Item Price", {"item_code": item.item}, "price_list_rate")
					if sale_value_of_pdt:
						total_sale_value += float(sale_value_of_pdt) * item.quantity
					else:
						frappe.throw(_("Selling price not set for item {0}").format(item.item))
						
		value_scrap = frappe.db.get_value("Process Definition", self.process_name, "value_scrap")
		if value_scrap:
			for item in self.scrap:
				if item.quantity >= 0:
					qty_of_total_production = float(qty_of_total_production + item.quantity)
					if self.costing_method == "Relative Sales Value":
						sale_value_of_pdt = frappe.db.get_value("Item Price", {"item_code": item.item},
																"price_list_rate")
						if sale_value_of_pdt:
							total_sale_value += float(sale_value_of_pdt) * item.quantity
						else:
							frappe.throw(_("Selling price not set for item {0}").format(item.item))
		# add Stock Entry Items for produced goods and scrap
		for item in self.finished_products:
			se = self.set_se_items(se, item, None, se.to_warehouse, True, qty_of_total_production, total_sale_value,
								   production_cost)
		for item in self.scrap:
			if value_scrap:
				se = self.set_se_items(se, item, None, self.scrap_warehouse, True, qty_of_total_production,
									   total_sale_value, production_cost)
			else:
				se = self.set_se_items(se, item, None, self.scrap_warehouse, False)
		return se

	@frappe.whitelist()
	def set_se_items(self, se, item, s_wh, t_wh, calc_basic_rate=False, qty_of_total_production=None,
					 total_sale_value=None, production_cost=None):
		if item.quantity >= 0:
			expense_account, cost_center = frappe.db.get_values("Company", self.company, \
																["default_expense_account", "cost_center"])[0]
			item_name, stock_uom, description = frappe.db.get_values("Item", item.item, \
																	 ["item_name", "stock_uom", "description"])[0]
			expense_account, cost_center = \
				frappe.db.get_values("Company", self.company, ["default_expense_account", "cost_center"])[0]
			item_name, stock_uom, description = \
				frappe.db.get_values("Item", item.item, ["item_name", "stock_uom", "description"])[0]

			item_expense_account, item_cost_center = (None,None)
			
			# frappe.db.get_value("Item Default",
			# 															 {'parent': item.item, 'company': self.company}, \
			# 															 {'parent': item.item, 'company': self.company},
			# 															 ["expense_account", "buying_cost_center"])

			# if not expense_account and not item_expense_account:
			# 	frappe.throw(
			# 		_("Please update default Default Cost of Goods Sold Account for company {0}").format(self.company))
			# if not cost_center and not item_cost_center:
			# 	frappe.throw(_("Please update default Cost Center for company {0}").format(self.company))
			se_item = se.append("items")
			se_item.item_code = item.item
			se_item.qty = item.quantity
			se_item.s_warehouse = s_wh
			se_item.t_warehouse = t_wh
			se_item.item_name = item_name
			se_item.description = description
			se_item.uom = stock_uom
			se_item.stock_uom = stock_uom
			se_item.expense_account = item_expense_account or expense_account
			se_item.cost_center = item_cost_center or cost_center
			# in stock uom
			se_item.transfer_qty = item.quantity
			se_item.conversion_factor = 1.00
			item_details = se.run_method("get_item_details", args=(frappe._dict(
				{"item_code": item.item, "company": self.company, "uom": stock_uom, 's_warehouse': s_wh})),
										 for_update=True)
			for f in ("uom", "stock_uom", "description", "item_name", "expense_account",
					  "cost_center", "conversion_factor"):
				se_item.set(f, item_details.get(f))

			if calc_basic_rate:
				if self.costing_method == "Physical Measurement":
					if self.costing_method == "Value Based Costing":
						se_item.basic_rate = production_cost / qty_of_total_production
				elif self.costing_method == "Relative Sales Value":
					sale_value_of_pdt = frappe.db.get_value("Item Price", {"item_code": item.item}, "price_list_rate")
					se_item.basic_rate = (float(sale_value_of_pdt) * float(production_cost)) / float(total_sale_value)
		return se

	@frappe.whitelist()	
	def make_stock_entry(self, status):
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.process_order = self.name

		if status == "Submitted":
			stock_entry.purpose = "Material Transfer for Manufacture"
			stock_entry.stock_entry_type = "Material Transfer for Manufacture"
			stock_entry = self.set_se_items_start(stock_entry)

		if status == "In Process":
			stock_entry.purpose = "Manufacture"
			stock_entry.stock_entry_type = "Manufacture"
			stock_entry = self.set_se_items_finish(stock_entry)

		return stock_entry.as_dict()
	@frappe.whitelist()	
	def add_item_in_table(self, table_value, table_name):
		self.set(table_name, [])
		for item in table_value:
			po_item = self.append(table_name, {})
			po_item.item = item.item
			po_item.item_name = item.item_name
			
@frappe.whitelist()			
def validate_items(se_items, po_items):
	# validate for items not in process order
	for se_item in se_items:
		if not filter(lambda x: x.item == se_item.item_code, po_items):
			frappe.throw(
				_("Item {0} - {1} cannot be part of this Stock Entry").format(se_item.item_code, se_item.item_name))
@frappe.whitelist()
def validate_material_qty(se_items, po_items):
	# TODO allow multiple raw material transfer?
	for material in po_items:
		qty = 0
		for item in se_items:
			if (material.item == item.item_code):
				qty += item.qty
		if qty != material.quantity:
			frappe.throw(_("Total quantity of Item {0} - {1} should be {2}").format(material.item, material.item,
																					material.quantity))
@frappe.whitelist()
def manage_se_submit(se, po):
	if po.docstatus == 0:
		frappe.throw(_("Submit the  Process Order {0} to make Stock Entries").format(po.name))
	if po.status == "Submitted":
		po.status = "In Process"
		po.start_dt = get_datetime()
	elif po.status == "In Process":
		po.status = "Completed"
	elif po.status in ["Completed", "Cancelled"]:
		frappe.throw("You cannot make entries against Completed/Cancelled Process Orders")
	po.flags.ignore_validate_update_after_submit = True
	po.save()
@frappe.whitelist()	
def manage_se_cancel(se, po):
	if po.status == "In Process":
		po.status = "Submitted"
	elif po.status == "Completed":
		try:
			validate_material_qty(se.items, po.finished_products)
			po.status = "In Process"
		except:
			frappe.throw("Please cancel the production stock entry first.")
	else:
		frappe.throw("Process order status must be In Process or Completed")
	po.flags.ignore_validate_update_after_submit = True
	po.save()
@frappe.whitelist()	
def validate_se_qty(se, po):
	validate_material_qty(se.items, po.materials)
	if po.status == "In Process":
		validate_material_qty(se.items, po.finished_products)
		validate_material_qty(se.items, po.scrap)

@frappe.whitelist()
def manage_se_changes(doc, method):
	if doc.process_order:
		po = frappe.get_doc("Process Order", doc.process_order)
		if method == "on_submit":
			if po.status == "Submitted":
				validate_items(doc.items, po.materials)
			elif po.status == "In Process":
				po_items = po.materials
				po_items.extend(po.finished_products)
				po_items.extend(po.scrap)
				validate_items(doc.items, po_items)
			validate_se_qty(doc, po)
			manage_se_submit(doc, po)
		elif method == "on_cancel":
			manage_se_cancel(doc, po)
   
# @frappe.whitelist()
# def Get_Purchase_Rate(item):
# 	query = """select  valuation_rate from `tabStock Ledger Entry` where item_code = %(items)s order by creation LIMIT 1"""
# 	data = frappe.db.sql(query, {"items": item},as_dict=1)
# 	return data

