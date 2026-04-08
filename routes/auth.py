from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import AppSetting, Staff, db

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def _get_passcode_hash():
    setting = AppSetting.query.filter_by(key="passcode").first()
    return setting.value if setting else None


def _set_passcode_hash(plain):
    setting = AppSetting.query.filter_by(key="passcode").first()
    if not setting:
        setting = AppSetting(key="passcode", value="")
        db.session.add(setting)
    setting.value = generate_password_hash(plain)
    db.session.commit()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not _get_passcode_hash():
        return redirect(url_for("auth.setup"))

    staffs = Staff.query.order_by(Staff.sort_order, Staff.name).all()

    if request.method == "POST":
        passcode = request.form.get("passcode", "")
        staff_name = request.form.get("staff_name", "").strip()
        stored = _get_passcode_hash()

        if staffs and not staff_name:
            flash("名前を選択してください", "danger")
        elif stored and check_password_hash(stored, passcode):
            session["logged_in"] = True
            session["staff_name"] = staff_name
            session.permanent = True
            flash(f"{staff_name} さん、おかえりなさい！", "success")
            return redirect(url_for("main.index"))
        else:
            flash("アカウントIDが正しくありません", "danger")

    return render_template("login.html", staffs=staffs)


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    if _get_passcode_hash():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        passcode = request.form.get("passcode", "").strip()
        confirm = request.form.get("confirm", "").strip()
        if not passcode:
            flash("アカウントIDを入力してください", "danger")
        elif passcode != confirm:
            flash("確認用と一致しません", "danger")
        else:
            _set_passcode_hash(passcode)
            session["logged_in"] = True
            session.permanent = True
            flash("アカウントIDを設定しました！", "success")
            return redirect(url_for("main.index"))

    return render_template("setup.html")


@auth_bp.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("staff_name", None)
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-passcode", methods=["GET", "POST"])
@login_required
def change_passcode():
    if request.method == "POST":
        current = request.form.get("current", "")
        new_pass = request.form.get("new_passcode", "").strip()
        confirm = request.form.get("confirm", "").strip()

        stored = _get_passcode_hash()
        if not check_password_hash(stored, current):
            flash("現在のアカウントIDが正しくありません", "danger")
        elif not new_pass:
            flash("新しいアカウントIDを入力してください", "danger")
        elif new_pass != confirm:
            flash("確認用と一致しません", "danger")
        else:
            _set_passcode_hash(new_pass)
            flash("アカウントIDを変更しました！", "success")
            return redirect(url_for("main.index"))

    return render_template("change_passcode.html")
