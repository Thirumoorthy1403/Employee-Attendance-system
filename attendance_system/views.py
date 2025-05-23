
from django.shortcuts import redirect, render, get_object_or_404
from .forms import AttendanceFormset, AttendanceSearchForm, EmployeeForm, AttendanceForm, EmployeeSearchForm
from django.contrib import messages
from .models import EmployeeAttendance, Employee
from django.db.models import Q
import datetime
# Create your views here.


def is_today_attendance():
    attendance = EmployeeAttendance.objects.filter(date=datetime.date.today())
    return [attendance,attendance.exists()]


def edit_today_attendance(request):
    employees = Employee.objects.all()
    if employees.exists():
        if request.method == 'POST':
            formset = AttendanceFormset(request.POST or None, initial=[{'employee': employee} for employee in employees ])
            if formset.is_valid():
                for form in formset:
                    form.save()
                messages.success(request, "Data is successfully saved !")
                return redirect("attendance_system:view_today_attendance")
            else:
                messages.info(request, formset.non_form_errors())
    
        else:
            if is_today_attendance()[1]:
                return redirect('attendance_system:view_today_attendance')
            formset = AttendanceFormset(initial=[{'employee': employee} for employee in employees])
        return render(request, 'edit_today_attendance.html', {'formset': formset})
    else:
        messages.warning(request, 'No employee data available.Please add an employee.')
        return redirect('attendance_system:employee_create')
    


def view_today_attendance(request):
    attendace , exists = is_today_attendance()
   
    if exists:
        return render(request,'view_today_attendance.html', {'attendance' : attendace })
    else:
        return redirect("attendance_system:edit_today_attendance")


def employees_listing(request):
    employee_search_form = EmployeeSearchForm(request.POST or None)
    employees = Employee.objects.all()
    no_data= None
    no_employee_exists = 'No employees exists in database' if not employees.exists() else None
    if request.method == 'POST':
        if employee_search_form.is_valid():
            name = employee_search_form.cleaned_data['name']
            department = employee_search_form.cleaned_data['departments']
            if department == 'A': 
                employees = Employee.objects.all()
                if name:
                    employees = employees.filter(name=name)
            elif name and department: 
                employees = Employee.objects.filter(Q(name=name) & Q(department=department))
            else:
                employees = Employee.objects.filter(Q(name=name) | Q(department=department))

    if len(employees) == 0:
        no_data = 'No employee data available'
    context = {
        'employees' : employees,
        'employee_search_form': employee_search_form,
        'no_data' : no_data,
        'no_employee_exists' : no_employee_exists
    }
    return render(request, 'employees_listing.html' , context)


def employee_attendance_details(request, empid):
    search_form = AttendanceSearchForm(request.POST or None)
    try:
        employee = get_object_or_404(Employee,pk=empid)
        attendance_qs = EmployeeAttendance.objects.filter(employee__id=empid).order_by('-date')
        data = 'all'
        no_data = 'No data exists for this employee' if len(attendance_qs) == 0 else None
        if request.method == 'POST' and no_data is None:
            if search_form.is_valid():
                date_from = request.POST.get('date_from')
                date_to = request.POST.get('date_to')
                if date_from > date_to:
                    messages.warning(request, 'Please select to date greater than from date.')
                
                else:
                    qs = EmployeeAttendance.objects.filter(Q(employee__id=empid) & Q(date__lte=date_to, date__gte=date_from))
                    if len(qs)==0:
                        messages.info(request, 'No data is available in this date range.')
                    else:
                        attendance_qs=qs
                        data = f'from {date_from} to {date_to}'

        context = {
            'search_form' : search_form,
            'attendance_qs' : attendance_qs,
            'employee' : employee,
            'data' : data,
            'no_data' : no_data

        }
        return render(request, 'employee_attendance_details.html', context)

    except:
        messages.warning(request, 'Something went wrong, try again !')
        return redirect('attendance_system:all_attendance_dashboard')



def employee_create(request):
    employee_form = EmployeeForm(request.POST or None)
    _,exists = is_today_attendance() 
    attendance_form = AttendanceForm(request.POST or None) if exists else None
    context = {
           'employee_form':employee_form, 
           'attendance_form': attendance_form,
           'form_type' : 'Add new employee'
    }
    if employee_form.is_valid():
        employee = employee_form.save() 
        if exists: 
            is_present = attendance_form.data['is_present']
            if is_present:
                instance = EmployeeAttendance.objects.create(is_present= is_present, employee=employee)
                instance.save() 
                messages.success(request, 'Employee added successfully and attendance details have been updated.')
                return redirect("attendance_system:all_attendance_dashboard")
            else:
                employee.delete() 
                return render(request, 'employee_form.html', context)
        messages.success(request, 'Employee added successfully!')
        return redirect("attendance_system:all_attendance_dashboard")
    
    return render(request, 'employee_form.html',context)


def employee_update(request, empid):
    try:
        employee= get_object_or_404(Employee, pk=empid)
        employee_form = EmployeeForm(request.POST or None, instance=employee)
        if employee_form.is_valid():
            employee_form.save()
            messages.success(request, 'Employee details updated successfully !')
            return redirect('attendance_system:all_attendance_dashboard')
        context = {
            'employee_form': employee_form,
            'form_type' : 'Update employee details'
            }
        return render(request, 'employee_form.html',context )
    except:
        messages.warning(request, 'Something went wrong, try again !')
        return redirect('attendance_system:all_attendance_dashboard')

def employee_delete(request, empid):
    try:
        employee= get_object_or_404(Employee, pk=empid)    
        employee.delete()
        messages.success(request, 'Employee deleted successfully !')
    except:
        messages.warning(request, 'Something went wrong, try again !')
    return redirect('attendance_system:all_attendance_dashboard')