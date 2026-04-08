from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models import Item, Stock, StockRecord, db

stock_bp = Blueprint("stock", __name__)


@stock_bp.route("/stock")
def stock_record_page():
    category = request.args.get("category", "")
    query = Item.query.order_by(Item.category, Item.sort_order, Item.name)
    if category:
        query = query.filter(Item.category == category)
    items = query.all()

    # Items needing reorder
    all_items = Item.query.order_by(Item.category, Item.sort_order, Item.name).all()
    order_needed = [i for i in all_items if i.status == "order"]
    low_items = [i for i in all_items if i.status == "low"]

    records = StockRecord.query.order_by(StockRecord.created_at.desc()).limit(50).all()

    categories = db.session.query(Item.category).distinct().order_by(Item.category).all()
    categories = [c[0] for c in categories]

    return render_template(
        "stock_record.html",
        items=items,
        records=records,
        categories=categories,
        selected_category=category,
        order_needed=order_needed,
        low_items=low_items,
    )


@stock_bp.route("/stock/in", methods=["POST"])
def stock_in():
    item_id = int(request.form.get("item_id"))
    quantity = int(request.form.get("quantity", 0))
    note = request.form.get("note", "").strip()

    if quantity > 0:
        stock = Stock.query.filter_by(item_id=item_id).first()
        if not stock:
            stock = Stock(item_id=item_id, quantity=0)
            db.session.add(stock)
        stock.quantity += quantity
        stock.updated_at = datetime.utcnow()

        operator = session.get("staff_name", "")
        record = StockRecord(item_id=item_id, record_type="in", quantity=quantity, operator=operator, note=note)
        db.session.add(record)
        db.session.commit()
        item = Item.query.get(item_id)
        flash(f"「{item.name}」を {quantity} 個 入庫しました！", "success")

    return redirect(url_for("stock.stock_record_page"))


@stock_bp.route("/stock/out", methods=["POST"])
def stock_out():
    item_id = int(request.form.get("item_id"))
    quantity = int(request.form.get("quantity", 0))
    note = request.form.get("note", "").strip()

    if quantity > 0:
        stock = Stock.query.filter_by(item_id=item_id).first()
        if not stock:
            stock = Stock(item_id=item_id, quantity=0)
            db.session.add(stock)
        stock.quantity = max(0, stock.quantity - quantity)
        stock.updated_at = datetime.utcnow()

        operator = session.get("staff_name", "")
        record = StockRecord(item_id=item_id, record_type="out", quantity=quantity, operator=operator, note=note)
        db.session.add(record)
        db.session.commit()
        item = Item.query.get(item_id)
        flash(f"「{item.name}」を {quantity} 個 出庫しました", "success")

    return redirect(url_for("stock.stock_record_page"))


@stock_bp.route("/stock/set", methods=["POST"])
def stock_set():
    item_id = int(request.form.get("item_id"))
    quantity = int(request.form.get("quantity", 0))
    note = request.form.get("note", "棚卸し").strip()

    stock = Stock.query.filter_by(item_id=item_id).first()
    if not stock:
        stock = Stock(item_id=item_id, quantity=0)
        db.session.add(stock)

    old_qty = stock.quantity
    stock.quantity = max(0, quantity)
    stock.updated_at = datetime.utcnow()

    diff = quantity - old_qty
    if diff != 0:
        record_type = "in" if diff > 0 else "out"
        record = StockRecord(
            item_id=item_id,
            record_type=record_type,
            quantity=abs(diff),
            operator=session.get("staff_name", ""),
            note=note,
        )
        db.session.add(record)

    db.session.commit()
    return redirect(url_for("stock.stock_record_page"))
