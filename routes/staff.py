from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import Staff, db

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/staff")
def staff_list():
    staffs = Staff.query.order_by(Staff.sort_order, Staff.name).all()
    return render_template("staff_manage.html", staffs=staffs)


@staff_bp.route("/staff/add", methods=["POST"])
def staff_add():
    name = request.form.get("name", "").strip()
    if name and not Staff.query.filter_by(name=name).first():
        staff = Staff(name=name)
        db.session.add(staff)
        db.session.commit()
        flash(f"「{name}」を登録しました！", "success")
    return redirect(url_for("staff.staff_list"))


@staff_bp.route("/staff/<int:staff_id>/edit", methods=["POST"])
def staff_edit(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    new_name = request.form.get("name", "").strip()
    if new_name and new_name != staff.name:
        staff.name = new_name
        db.session.commit()
        flash(f"「{new_name}」に更新しました！", "success")
    return redirect(url_for("staff.staff_list"))


@staff_bp.route("/staff/<int:staff_id>/delete", methods=["POST"])
def staff_delete(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    name = staff.name
    db.session.delete(staff)
    db.session.commit()
    flash(f"「{name}」を削除しました", "danger")
    return redirect(url_for("staff.staff_list"))
