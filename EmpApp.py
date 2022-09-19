from sqlite3 import Cursor
from types import MethodDescriptorType
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
import datetime
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


#Main
@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route("/about", methods=['GET', 'POST'])
def about():
    cursor = db_conn.cursor()

    select_sql = "SELECT empName, s3_url, role, department FROM employee WHERE role = %s"

    cursor.execute(select_sql, ("Director"))
    result = cursor.fetchall()

    cursor.close()
    
    return render_template('about.html', empList = result)

#Index
@app.route("/empIndex", methods=['GET', 'POST'])
def empIndex():
    cursor = db_conn.cursor()

    select_sql = "SELECT * FROM employee"

    cursor.execute(select_sql)
    result = cursor.fetchall()

    cursor.close()
    
    return render_template('employees/index.html', empList = result)

@app.route("/attendanceIndex", methods=['GET', 'POST'])
def attendanceIndex():
    cursor = db_conn.cursor()

    select_sql = "SELECT employee.empName, attendance.* FROM attendance INNER JOIN employee ON attendance.empID = employee.empID"

    cursor.execute(select_sql)
    result = cursor.fetchall()

    cursor.close()
    
    return render_template('attendances/index.html', attendanceList = result)

@app.route("/workforceIndex", methods=['GET', 'POST'])
def workforceIndex():
    cursor = db_conn.cursor()

    select_sql = "SELECT * FROM workforce"

    select_sql = "SELECT employee.empName, workforce.* FROM workforce INNER JOIN employee ON workforce.empID = employee.empID"

    cursor.execute(select_sql)
    result = cursor.fetchall()

    cursor.close()
    
    return render_template('workforces/index.html', workforceList = result)

@app.route("/performanceIndex", methods=['GET', 'POST'])
def performanceIndex():    
    cursor = db_conn.cursor()

    select_sql = "SELECT employee.empName, performance.* FROM performance INNER JOIN employee ON performance.empID = employee.empID"

    cursor.execute(select_sql)
    result = cursor.fetchall()

    cursor.close()

    return render_template('performances/index.html', performanceList = result)

@app.route("/payrollIndex", methods=['GET', 'POST'])
def payrollIndex():
    cursor = db_conn.cursor()

    select_sql = "SELECT employee.empName, payroll.* FROM payroll INNER JOIN employee ON payroll.empID = employee.empID"

    cursor.execute(select_sql)
    result = cursor.fetchall()

    cursor.close()
    
    return render_template('payrolls/index.html', payrollList = result)


#Employee Module
@app.route("/empCreate", methods=['GET', 'POST'])
def empCreate():
    return render_template('employees/create.html')
    
@app.route("/empStore", methods=['POST'])
def empStore():    
    empName = request.form['empName']
    contact = request.form['contact']
    email = request.form['email']
    address = request.form['address']
    profile = request.files['profile']
    role = request.form['role']
    department = request.form['department']
    dateCreated = datetime.datetime.now()

    cursor = db_conn.cursor()

    select_lastid_sql = "SELECT total_emp FROM employee ORDER BY total_emp DESC LIMIT 1"

    cursor.execute(select_lastid_sql)
    result_lastid = cursor.fetchone()
    id = result_lastid[0]
    total_emp = int(id)+1
        
    empID = "E" + str(total_emp)

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        
    try:
        if profile.filename == "":
            s3_url = "https://ainisha-employee.s3.amazonaws.com/images/default.jpg"
        else:
            # Upload image file in S3 #
            emp_image_file_name_in_s3 = "emp-id-" + str(empID) + "_image_file_"
            s3 = boto3.resource('s3')
            date_time = datetime.datetime.now()
            datetime_object = date_time.strftime("%d_%m_%Y_%H_%M_%S")

            try:
                s3.Bucket(custombucket).put_object(Key="profile/" + emp_image_file_name_in_s3 +  datetime_object + "." + profile.filename, Body=profile)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                s3_url = "https://{0}.s3.amazonaws.com/profile/{1}".format(
                    custombucket,
                    emp_image_file_name_in_s3 + datetime_object + "." + profile.filename
                )

            except Exception as e:
                return str(e)

        cursor.execute(insert_sql, (empID, empName, s3_url, contact, email, address, role, department, dateCreated, total_emp))
        db_conn.commit()

    finally:                
        cursor.close()

    return empIndex()

@app.route("/empEdit", methods=['POST'])
def empEdit():
    empID = request.form['empID']
    empName = request.form['empName']
    
    cursor = db_conn.cursor()

    select_sql = "SELECT * FROM employee WHERE empID = %s AND empName = %s"
    cursor.execute(select_sql, (empID, empName))
    result = cursor.fetchall()
    
    cursor.close()

    return render_template('employees/update.html', empEdit = result)

@app.route("/empUpdate", methods=['POST'])
def empUpdate():
    empID = request.form['empID']
    empName = request.form['empName']
    contact = request.form['contact']
    email = request.form['email']
    address = request.form['address']
    profile = request.files['profile']
    role = request.form['role']
    department = request.form['department']
    s3_url = request.form['s3_url']

    cursor = db_conn.cursor()

    update_sql = "UPDATE employee SET empName = %s, s3_url = %s, contact = %s, email = %s, address = %s, role = %s, department = %s WHERE empID = %s"

    try:
        if profile.filename != "":
            # Upload image file in S3 #
            emp_image_file_name_in_s3 = "emp-id-" + str(empID) + "_image_file_"
            s3 = boto3.resource('s3')
            date_time = datetime.datetime.now()
            datetime_object = date_time.strftime("%d_%m_%Y_%H_%M_%S")

            try:
                s3.Bucket(custombucket).put_object(Key="profile/" + emp_image_file_name_in_s3 +  datetime_object + "." + profile.filename, Body=profile)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                s3_url = "https://{0}.s3.amazonaws.com/profile/{1}".format(
                    custombucket,
                    emp_image_file_name_in_s3 + datetime_object + "." + profile.filename
                )                

            except Exception as e:
                return str(e)

        cursor.execute(update_sql, (empName, s3_url, contact, email, address, role, department, empID))
        db_conn.commit()

    finally:        
        cursor.close()

    return empIndex()

@app.route("/empDelete", methods=['POST'])
def empDelete():
    empID = request.form['empID']
    empName = request.form['empName']

    cursor = db_conn.cursor()

    delete_sql = "DELETE FROM employee WHERE empID = %s AND empName = %s"

    try:
        cursor.execute(delete_sql, (empID, empName))
        db_conn.commit()

    finally:
        cursor.close()

    return empIndex()


#Attendance Module
@app.route("/attendanceCreate", methods=['GET', 'POST'])
def attendanceCreate():
    cursor = db_conn.cursor()

    select_sql = "SELECT * FROM employee"

    cursor.execute(select_sql)
    result = cursor.fetchall()

    cursor.close()
    
    return render_template('attendances/create.html', empList = result)

@app.route("/attendanceStore", methods=['POST'])
def attendanceStore():
    empID = request.form['empID']
    date = request.form['date'] 
    checkin = datetime.datetime.strptime(request.form['checkin'],"%H:%M")
    checkout = datetime.datetime.strptime(request.form['checkout'],"%H:%M")
    basehour_0 = datetime.datetime.strptime("00:00","%H:%M")
    basehour_1 = datetime.datetime.strptime("08:00","%H:%M")

    workhour = checkout - checkin
    basehour = basehour_1 - basehour_0

    overtime =  workhour - basehour

    cursor = db_conn.cursor()

    select_emp_sql = "SELECT empName FROM employee WHERE empID = %s"
    cursor.execute(select_emp_sql, (empID))
    result_emp = cursor.fetchone()

    insert_sql = "INSERT INTO attendance (empID, date, checkin, checkout, workhour, overtime) VALUES (%s, %s, %s, %s, %s, %s)"

    try:
        cursor.execute(insert_sql, (empID, date, checkin, checkout, workhour, overtime))
        db_conn.commit()

    finally:
        cursor.close()

    return attendanceIndex()


#WorkForce Module
@app.route("/workforceCreate", methods=['GET', 'POST'])
def workforceCreate():
    cursor = db_conn.cursor()

    select_sql = "SELECT * FROM employee"

    cursor.execute(select_sql)
    result = cursor.fetchall()

    cursor.close()
    
    return render_template('workforces/create.html', empList = result)

@app.route("/workforceStore", methods=['POST'])
def workforceStore():
    empID = request.form['empID']
    branch = request.form['branch'] 
    task = request.form['task']
    cursor = db_conn.cursor()

    insert_sql = "INSERT INTO workforce (empID, branch, task) VALUES (%s, %s, %s)"

    try:
        cursor.execute(insert_sql, (empID, branch, task))
        db_conn.commit()

    finally:
        cursor.close()

    return workforceIndex()

@app.route("/workforceEdit", methods=['POST'])
def workforceEdit():
    empID = request.form['empID']
    workforceID = request.form['workforceID']
    
    cursor = db_conn.cursor()

    select_sql = "SELECT employee.empName, workforce.* FROM workforce INNER JOIN employee ON workforce.empID = employee.empID WHERE workforce.workforceID = %s AND workforce.empID = %s"

    cursor.execute(select_sql, (workforceID, empID))
    result = cursor.fetchall()
    
    cursor.close()

    return render_template('workforces/update.html', workforceEdit = result)

@app.route("/workforceUpdate", methods=['POST'])
def workforceUpdate():
    workforceID = request.form['workforceID']
    branch = request.form['branch']
    task = request.form['task']

    cursor = db_conn.cursor()

    update_sql = "UPDATE workforce SET branch = %s, task = %s WHERE workforceID = %s"

    try:
        cursor.execute(update_sql, (branch, task, workforceID))
        db_conn.commit()

    finally:        
        cursor.close()

    return workforceIndex()

@app.route("/workforceDelete", methods=['POST'])
def workforceDelete():
    workforceID = request.form['workforceID']

    cursor = db_conn.cursor()

    delete_sql = "DELETE FROM workforce WHERE workforceID = %s"

    try:
        cursor.execute(delete_sql, (workforceID))
        db_conn.commit()

    finally:
        cursor.close()

    return workforceIndex()


#Performance Module
@app.route("/performanceCreate", methods=['GET', 'POST'])
def performanceCreate():
    empID = request.form['empID']
    empName = request.form['empName']
    
    cursor = db_conn.cursor()

    select_sql = "SELECT * FROM employee WHERE empID = %s AND empName = %s"

    cursor.execute(select_sql, (empID, empName))
    result = cursor.fetchall()

    cursor.close()

    return render_template('performances/create.html', empRate = result)

@app.route("/performanceStore", methods=['POST'])
def performanceStore():
    empID = request.form['empID']
    empName = request.form['empName']
    grade = request.form['grade']
    bonus = request.form['bonus']
    remark = request.form['remark']

    cursor = db_conn.cursor()

    insert_sql = "INSERT INTO performance (empID, grade, bonus, remark) VALUES (%s, %s, %s, %s)"

    try:
        cursor.execute(insert_sql, (empID, grade, bonus, remark))
        db_conn.commit()

    finally:
        cursor.close()

    return performanceIndex()

@app.route("/performanceDelete", methods=['POST'])
def performanceDelete():
    performanceID = request.form['performanceID']
    empID = request.form['empID']

    cursor = db_conn.cursor()

    delete_sql = "DELETE FROM performance WHERE performanceID = %s AND empID = %s"

    try:
        cursor.execute(delete_sql, (performanceID, empID))
        db_conn.commit()

    finally:        
        cursor.close()

    return performanceIndex()


#Payroll Module
@app.route("/payrollCreate", methods=['GET', 'POST'])
def payrollCreate():
    cursor = db_conn.cursor()

    select_sql = "SELECT * FROM employee"

    cursor.execute(select_sql)
    result = cursor.fetchall()

    cursor.close()
    
    return render_template('payrolls/create.html', empList = result)

@app.route("/payrollStore", methods=['POST'])
def payrollStore():
    empID = request.form['empID']
    payDate = request.form['date'] 
    payTime = request.form['time']
    salary = request.form['salary']
    rate = request.form['rate']

    cursor = db_conn.cursor()

    select_emp_sql = "SELECT empName FROM employee WHERE empID = %s"

    select_overtime_sql = "SELECT SUM(overtime) FROM attendance WHERE empID = %s"

    try:
        cursor.execute(select_emp_sql, (empID))
        result_emp = cursor.fetchone()

        cursor.execute(select_overtime_sql, (empID))
        result_overtime = cursor.fetchone()
        overtime = float(result_overtime[0])

        calculate = float(salary) + float(overtime) * float(rate)
        netpay = float(calculate)

        insert_sql = "INSERT INTO payroll (empID, payDate, payTime, salary, overtime, rate, netpay) VALUES (%s, %s, %s, %s, %s, %s, %s)"

        cursor.execute(insert_sql, (empID, payDate, payTime, salary, overtime, rate, netpay))
        db_conn.commit()

    finally:
        cursor.close()

    return payrollIndex()

@app.route("/payrollDelete", methods=['POST'])
def payrollDelete():
    payrollID = request.form['payrollID']
    empID = request.form['empID']

    cursor = db_conn.cursor()

    delete_sql = "DELETE FROM payroll WHERE payrollID = %s AND empID = %s"

    try:
        cursor.execute(delete_sql, (payrollID, empID))
        db_conn.commit()

    finally:        
        cursor.close()

    return payrollIndex()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
