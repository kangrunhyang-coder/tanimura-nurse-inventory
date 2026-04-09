from flask import Blueprint, redirect, render_template, request, url_for

from models import Item, Order, Stock, StockRecord, db, now_jst

order_bp = Blueprint("order", __name__)


@order_bp.route("/orders")
def order_list():
    tab = request.args.get("tab", "pending")

    pending_orders = (
        Order.query.filter_by(status="pending")
        .join(Item)
        .order_by(Item.category, Item.name)
        .all()
    )
    ordered_orders = (
        Order.query.filter_by(status="ordered")
        .join(Item)
        .order_by(Order.ordered_at.desc())
        .all()
    )
    received_orders = (
        Order.query.filter_by(status="received")
        .join(Item)
        .order_by(Order.received_at.desc())
        .limit(50)
        .all()
    )

    # Items that need ordering but don't have a pending/ordered order
    order_needed_items = []
    for item in Item.query.all():
        if item.status == "order":
            has_open = Order.query.filter(
                Order.item_id == item.id,
                Order.status.in_(["pending", "ordered"]),
            ).first()
            if not has_open:
                order_needed_items.append(item)

    return render_template(
        "order_list.html",
        pending_orders=pending_orders,
        ordered_orders=ordered_orders,
        received_orders=received_orders,
        order_needed_items=order_needed_items,
        tab=tab,
    )


@order_bp.route("/orders/create", methods=["POST"])
def order_create():
    item_id = int(request.form.get("item_id"))
    quantity = int(request.form.get("quantity", 1))
    note = request.form.get("note", "").strip()

    order = Order(item_id=item_id, quantity=quantity, status="pending", note=note)
    db.session.add(order)
    db.session.commit()

    return redirect(url_for("order.order_list"))


@order_bp.route("/orders/<int:order_id>/status", methods=["POST"])
def order_update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")

    if new_status == "ordered":
        order.status = "ordered"
        order.ordered_at = now_jst()
    elif new_status == "received":
        order.status = "received"
        order.received_at = now_jst()

        # Auto stock-in on receive
        auto_in = request.form.get("auto_stock_in")
        if auto_in:
            stock = Stock.query.filter_by(item_id=order.item_id).first()
            if not stock:
                stock = Stock(item_id=order.item_id, quantity=0)
                db.session.add(stock)
            stock.quantity += order.quantity
            stock.updated_at = now_jst()

            record = StockRecord(
                item_id=order.item_id,
                record_type="in",
                quantity=order.quantity,
                note="発注入荷",
            )
            db.session.add(record)
    elif new_status == "pending":
        order.status = "pending"
        order.ordered_at = None
        order.received_at = None

    db.session.commit()
    return redirect(url_for("order.order_list"))


@order_bp.route("/orders/<int:order_id>/delete", methods=["POST"])
def order_delete(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for("order.order_list"))


@order_bp.route("/orders/bulk-create", methods=["POST"])
def order_bulk_create():
    item_ids = request.form.getlist("item_ids")
    for item_id in item_ids:
        existing = Order.query.filter_by(item_id=int(item_id), status="pending").first()
        if not existing:
            order = Order(item_id=int(item_id), quantity=1, status="pending")
            db.session.add(order)
    db.session.commit()
    return redirect(url_for("order.order_list"))
