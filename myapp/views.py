import sys,json,os,datetime,csv
from django.contrib import admin
from django.template.context import RequestContext
from django.shortcuts import render,render_to_response
from django.contrib import auth
from form import AddForm,LoginForm,Logquery,CaptchaTestForm
from captcha.fields import CaptchaField,CaptchaStore
from captcha.helpers import captcha_image_url
from django.http import HttpResponse,HttpResponseRedirect,StreamingHttpResponse
from django.contrib.auth.decorators import login_required,permission_required
from myapp.models import Db_name,Db_account,Db_instance,Oper_log
path='./myapp/include'
sys.path.insert(0,path)
import function as func
# Create your views here.
'''
class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)
'''

@login_required(login_url='/accounts/login/')
def index(request):
    return render(request, 'include/base.html')


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/accounts/login/")

@login_required(login_url='/accounts/login/')
@permission_required('myapp.can_log_query', login_url='/')
def log_query(request):
    #show every dbtags
    #obj_list = func.get_mysql_hostlist(request.user.username,'log')
    #show dbtags permitted to the user
    obj_list = func.get_mysql_hostlist(request.user.username)
    optype_list = func.get_op_type()
    if request.method == 'POST' :
        print func.get_client_ip(request)
        form = Logquery(request.POST)
        if form.is_valid():
            begintime = form.cleaned_data['begin']
            endtime = form.cleaned_data['end']
            hosttag = request.POST['hosttag']
            optype = request.POST['optype']
            print hosttag
            data = func.get_log_data(hosttag,optype,begintime,endtime)
            return render(request,'log_query.html',{'form': form,'objlist':obj_list,'optypelist':optype_list,'datalist':data})
        else:
            print "not valid"
            return render(request,'log_query.html',{'form': form,'objlist':obj_list,'optypelist':optype_list})
    else:
        form = Logquery()
        return render(request, 'log_query.html', {'form': form,'objlist':obj_list,'optypelist':optype_list})



@login_required(login_url='/accounts/login/')
@permission_required('myapp.can_mysql_query', login_url='/')
def mysql_query(request):
    #print request.user.username
    print request.user.has_perm('myapp.can_mysql_query')
    obj_list = func.get_mysql_hostlist(request.user.username)
    if request.method == 'POST':
        form = AddForm(request.POST)
        if form.is_valid():
            a = form.cleaned_data['a']
            c = request.POST['cx']
            try:
                #show explain
                if request.POST['explain']== u'1':
                    explaintag = request.POST['explain']
                    a = func.check_explain (a)
                    (data_mysql,collist,dbname) = func.get_mysql_data(c,a,request.user.username,request)
                    return render(request,'mysql_query.html',{'form': form,'objlist':obj_list,'data_list':data_mysql,'col':collist,'choosed_host':c,'dbname':dbname})
            except Exception,e:
                try:
                #export csv
                    if request.POST['export']== u'1':
                        a,numlimit = func.check_mysql_query(a,request.user.username,'export')
                        (data_mysql,collist,dbname) = func.get_mysql_data(c,a,request.user.username,request,numlimit)
                        pseudo_buffer = Echo()
                        writer = csv.writer(pseudo_buffer)
                        response = StreamingHttpResponse((writer.writerow(row) for row in data_mysql),content_type="text/csv")
                        response['Content-Disposition'] = 'attachment; filename="export.csv"'
                        return response
                except Exception,e:
                #get nomal query
                    a,numlimit = func.check_mysql_query(a,request.user.username)
                    (data_mysql,collist,dbname) = func.get_mysql_data(c,a,request.user.username,request,numlimit)
                    return render(request,'mysql_query.html',{'form': form,'objlist':obj_list,'data_list':data_mysql,'col':collist,'choosed_host':c,'dbname':dbname})
        else:
            return render(request, 'mysql_query.html', {'form': form,'objlist':obj_list})
    else:
        form = AddForm()
        return render(request, 'mysql_query.html', {'form': form,'objlist':obj_list})

class Echo(object):
    """An object that implements just the write method of the file-like interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def some_streaming_csv_view(request):
    """A view that streams a large CSV file."""
    # Generate a sequence of rows. The range is based on the maximum number of
    # rows that can be handled by a single sheet in most spreadsheet
    # applications.
    data = (["Row {}".format(idx), str(idx)] for idx in range(65536))
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in data),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="test.csv"'
    return response




@login_required(login_url='/accounts/login/')
@permission_required('myapp.can_see_execview', login_url='/')
def mysql_exec(request):
    #print request.user.username
    obj_list = func.get_mysql_hostlist(request.user.username,'exec')
    if request.method == 'POST':
        form = AddForm(request.POST)
        if form.is_valid():
            a = form.cleaned_data['a']
            c = request.POST['cx']
            a = func.check_mysql_exec(a,request)
            print a
            (data_mysql,collist,dbname) = func.run_mysql_exec(c,a,request.user.username,request)
            #print request.POST
            return render(request,'mysql_exec.html',{'form': form,'objlist':obj_list,'data_list':data_mysql,'col':collist,'choosed_host':c,'dbname':dbname})
        else:
            return render(request, 'mysql_exec.html', {'form': form,'objlist':obj_list})
    else:
        form = AddForm()
        return render(request, 'mysql_exec.html', {'form': form,'objlist':obj_list})

def chapt(request):
    if request.GET.get('newsn')=='1':
        csn=CaptchaStore.generate_key()
        cimageurl= captcha_image_url(csn)
        return HttpResponse(cimageurl)
    if request.POST:
        form = CaptchaTestForm(request.POST)
        # Validate the form: the captcha field will automatically
        # check the input
        if form.is_valid():
            human = True
    else:
        form = CaptchaTestForm()
    return render_to_response('chaptcha.html',{'form':form})


def login(request):
    if request.user.is_authenticated():
        return render(request, 'include/base.html')
    else:
        if request.method == 'GET':
            form = LoginForm()
            if request.GET.get('newsn')=='1':
                csn=CaptchaStore.generate_key()
                cimageurl= captcha_image_url(csn)
                return HttpResponse(cimageurl)
            else:
                return render_to_response('login.html', RequestContext(request, {'form': form}))
        else:
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = auth.authenticate(username=username, password=password)
                if user is not None and user.is_active:
                    auth.login(request, user)
                    return render(request,'include/base.html')
                else:
                    return render_to_response('login.html', RequestContext(request, {'form': form,'password_is_wrong':True}))
            else:
                return render_to_response('login.html', RequestContext(request, {'form': form}))




