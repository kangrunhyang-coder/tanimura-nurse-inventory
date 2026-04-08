from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import Area, InventoryCheck, InventoryCheckItem, Item, Stock, StockRecord, db

check_bp = Blueprint("check", __name__)


@check_bp.route("/check")
def check_top():
    # Get areas from Area model
    area_objs = Area.query.order_by(Area.sort_order, Area.name).all()
    areas = [a.name for a in area_objs]

    # Items with no area
    no_area_count = Item.query.filter((Item.area == "") | (Item.area.is_(None))).count()

    # Next check date info
    today = datetime.utcnow()
    day = today.day
    if day <= 5:
        next_check = 5
    elif day <= 15:
        next_check = 15
    elif day <= 25:
        next_check = 25
    else:
        next_check = 5  # next month

    is_check_day = day in (5, 15, 25)

    # Recent checks
    recent_checks = InventoryCheck.query.order_by(InventoryCheck.checked_at.desc()).limit(20).all()

    # Area item counts
    area_counts = {}
    for area in areas:
        area_counts[area] = Item.query.filter(Item.area == area).count()

    return render_template(
        "check_top.html",
        areas=areas,
        area_counts=area_counts,
        no_area_count=no_area_count,
        next_check=next_check,
        is_check_day=is_check_day,
        recent_checks=recent_checks,
        today=today,
    )


@check_bp.route("/check/area/<path:area_name>")
def check_area(area_name):
    if area_name == "__none__":
        items = Item.query.filter((Item.area == "") | (Item.area.is_(None))).order_by(Item.category, Item.sort_order, Item.name).all()
        display_area = "未設定エリア"
    else:
        items = Item.query.filter(Item.area == area_name).order_by(Item.category, Item.sort_order, Item.name).all()
        display_area = area_name

    return render_template(
        "check_area.html",
        items=items,
        area_name=area_name,
        display_area=display_area,
    )


@check_bp.route("/check/area/<path:area_name>/save", methods=["POST"])
def check_save(area_name):
    checker_name = request.form.get("checker_name", "").strip()
    note = request.form.get("note", "").strip()

    if not checker_name:
        checker_name = "未記入"

    actual_area = "" if area_name == "__none__" else area_name

    check = InventoryCheck(
        area=actual_area if actual_area else "未設定エリア",
        checker_name=checker_name,
        note=note,
    )
    db.session.add(check)
    db.session.flush()

    item_ids = request.form.getlist("item_ids")
    for item_id_str in item_ids:
        item_id = int(item_id_str)
        actual_qty = int(request.form.get(f"qty_{item_id}", 0))
        item = Item.query.get(item_id)
        system_qty = item.quantity if item else 0
        diff = actual_qty - system_qty

        check_item = InventoryCheckItem(
            check_id=check.id,
            item_id=item_id,
            system_quantity=system_qty,
            actual_quantity=actual_qty,
            difference=diff,
        )
        db.session.add(check_item)

        # Update actual stock
        stock = Stock.query.filter_by(item_id=item_id).first()
        if not stock:
            stock = Stock(item_id=item_id, quantity=0)
            db.session.add(stock)

        if diff != 0:
            stock.quantity = max(0, actual_qty)
            stock.updated_at = datetime.utcnow()
            record = StockRecord(
                item_id=item_id,
                record_type="in" if diff > 0 else "out",
                quantity=abs(diff),
                note=f"在庫チェック（{checker_name}）",
            )
            db.session.add(record)

    db.session.commit()
    flash(f"「{check.area}」の在庫チェックを保存しました！", "success")
    return redirect(url_for("check.check_detail", check_id=check.id))


@check_bp.route("/check/history")
def check_history():
    checks = InventoryCheck.query.order_by(InventoryCheck.checked_at.desc()).all()
    return render_template("check_history.html", checks=checks)


@check_bp.route("/check/<int:check_id>")
def check_detail(check_id):
    check = InventoryCheck.query.get_or_404(check_id)
    return render_template("check_detail.html", check=check)


@check_bp.route("/check/<int:check_id>/delete", methods=["POST"])
def check_delete(check_id):
    check = InventoryCheck.query.get_or_404(check_id)
    db.session.delete(check)
    db.session.commit()
    return redirect(url_for("check.check_history"))
