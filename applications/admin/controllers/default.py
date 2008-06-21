# This sees request, response, session, expose, redirect, HTTP

############################################################
### import required modules/functions
############################################################
from gluon.fileutils import listdir,cleanpath,tar,tar_compiled,untar,fix_newlines
from gluon.languages import findT, update_all_languages
from gluon.myregex import *
from gluon.restricted import *
from gluon.contrib.markdown import WIKI
from gluon.compileapp import compile_application, remove_compiled_application
import time,os,sys,re,urllib,socket


############################################################
### make sure administrator is on localhost
############################################################

http_host = request.env.http_host.split(':')[0]

try:
     from gluon.contrib.gql import GQLDB
     session_db=GQLDB()
     session.connect(request,response,db=session_db)
     hosts=(http_host,)
except:
     hosts=(http_host,socket.gethostname(),socket.gethostbyname(http_host))

remote_addr = request.env.remote_addr
if remote_addr not in hosts:
    raise HTTP(200,T('Admin is disabled because unsecure channel'))
if request.env.http_x_forwarded_for or \
   request.env.wsgi_url_scheme in ['https','HTTPS']:
    response.cookies[response.session_id_name]['secure']=True

############################################################
### generate menu
############################################################

_f=request.function
response.menu=[(T('site'),_f=='site','/%s/default/site'%request.application)]
if request.args:
    _t=(request.application,request.args[0])   
    response.menu.append((T('about'),_f=='about','/%s/default/about/%s'%_t))
    response.menu.append((T('design'),_f=='design','/%s/default/design/%s'%_t))
    response.menu.append((T('errors'),_f=='errors','/%s/default/errors/%s'%_t))    
if not session.authorized: response.menu=[(T('login'),True,'')]
else: response.menu.append((T('logout'),False,'/%s/default/logout'%request.application))
response.menu.append((T('help'),False,'/examples/default/index'))

############################################################
### exposed functions
############################################################

def apath(path=''):
    from gluon.fileutils import up
    opath=up(request.folder)
    #TODO: This path manipulation is very OS specific.
    while path[:3]=='../': opath,path=up(opath),path[3:]
    return os.path.join(opath,path).replace('\\','/')

try:
    _config={}
    port=int(request.env.server_port)
    restricted(open(apath('../parameters_%i.py'%port),'r').read(),_config)
    if not _config.has_key('password') or not _config['password']:
        raise HTTP(200,T('admin disabled because no admin password'))
except: raise HTTP(200,T('admin disabled because unable to access password file'))

############################################################
### session expiration
############################################################

t0=time.time()
if session.authorized:
    if session.last_time and session.last_time<t0-EXPIRATION:
        session.flash=T('session expired')
        session.authorized=False
    else: session.last_time=t0

if not session.authorized and not request.function=='index': 
    if request.env.query_string: query_string='?'+request.env.query_string
    else: query_string=''
    url=request.env.path_info+query_string
    redirect(URL(r=request,f='index',vars=dict(send=url)))

def index():
    """ admin controller function """
    send=request.vars.send
    if not send: send=URL(r=request,f='site')
    if request.vars.password:
        if _config['password']==CRYPT()(request.vars.password)[0]:
            session.authorized=True
            if CHECK_VERSION:
                try:        
                    version=urllib.urlopen('http://mdp.cti.depaul.edu/examples/default/version').read()
                    myversion=open(apath('../VERSION'),'r').read()
                    if version>myversion: session.flash='A new version of web2py is available, you should upgrade at http://mdp.cti.depaul.edu/examples'
                except: pass
            session.last_time=t0
            redirect(send)
        else: response.flash=T('invalid password')
    apps=[file for file in os.listdir(apath()) if file.find('.')<0]    
    return dict(apps=apps,send=send)

def logout():
    """ admin controller function """
    session.authorized=None
    redirect(URL(r=request,f='index'))

def site():
    """ admin controller function """
    if request.vars.filename and not request.vars.has_key('file'):
        try:
            appname=cleanpath(request.vars.filename).replace('.','_')
            path=apath(appname)
            os.mkdir(path)
            untar('welcome.tar',path)
            response.flash=T('new application "%(appname)s" created',dict(appname=appname))
        except:
            response.flash=T('unable to create new application "%(appname)s"',dict(appname=request.vars.filename))
    elif request.vars.has_key('file') and not request.vars.filename:
        response.flash=T('you must specify a name for the uploaded application')
    elif request.vars.filename and request.vars.has_key('file'):
        try:
            appname=cleanpath(request.vars.filename).replace('.','_')
            tarname=apath('../deposit/%s.tar' % appname)
            open(tarname,'wb').write(request.vars.file.file.read())
            path=apath(appname)
            os.mkdir(path)
            untar(tarname,path)
            fix_newlines(path)
            response.flash=T('application %(appname)s installed',dict(appname=appname))
        except:
            response.flash=T('unable to install application "%(appname)s"',dict(appname=request.vars.filename))
    regex=re.compile('^\w+$')
    apps=[file for file in os.listdir(apath()) if regex.match(file)]
    return dict(app=None,apps=apps)

def pack():        
    """ admin controller function """
    try: 
        app=request.args[0]
        filename=apath('../deposit/%s.tar' % app)
        tar(filename,apath(app),'^[\w\.\-]+$')
    except:
        session.flash=T('internal error')
        redirect(URL(r=request,f='site'))
    response.headers['Content-Type']='application/x-tar'
    response.headers['Content-Disposition']='attachment; filename=web2py.app.%s.tar'%app
    return open(filename,'rb').read()

def pack_compiled():        
    """ admin controller function """
    try: 
        app=request.args[0]
        filename=apath('../deposit/%s.tar' % app)
        tar_compiled(filename,apath(app),'^[\w\.\-]+$')
    except:
        session.flash=T('internal error')
        redirect(URL(r=request,f='site'))
    response.headers['Content-Type']='application/x-tar'
    response.headers['Content-Disposition']='attachment; filename=web2py.app.%s.compiled.tar'%app
    return open(filename,'rb').read()

def uninstall():
    """ admin controller function """
    try:
        app=request.args[0]
        if not request.vars.has_key('delete'): return dict(app=app)
        elif request.vars['delete']!='YES':
             #TODO: It looks like this was overlooked.  When it gets filled in, don't forget to T() it.  -mdm 6/9/08
             session.flash=''
             redirect(URL(r=request,f='site'))        
        filename=apath('../deposit/%s.tar' % app )
        path=apath(app)
        tar(filename,path,'^[\w\.]+$')
        for root,dirs,files in os.walk(path,topdown=False):
            for name in files: os.remove(os.path.join(root,name))
            for name in dirs: os.rmdir(os.path.join(root,name))
        os.rmdir(path)
        session.flash=T('application "%(appname)s" uninstalled',dict(appname=app))
    except:
        session.flash=T('unable to uninstall "%(appname)s"',dict(appname=app))
    redirect(URL(r=request,f='site'))

def cleanup():        
    """ admin controller function """
    app=request.args[0]
    files=listdir(apath('%s/errors/' % app),'^\d.*$',0)
    for file in files: os.unlink(file)
    files=listdir(apath('%s/sessions/' % app),'\d.*',0)
    for file in files: os.unlink(file)
    session.flash=T("cache, errors and sessions cleaned")
    files=listdir(apath('%s/cache/' % app),'cache.*',0)
    for file in files: 
        try: os.unlink(file)
        except: session.flash=T("cache is in use, errors and sessions cleaned")
    redirect(URL(r=request,f='site'))

def compile_app():
    """ admin controller function """
    app=request.args[0]
    folder=apath(app)
    try:
        compile_application(folder)
        session.flash=T('application compiled')
    except Exception, e:
        remove_compiled_application(folder)
        session.flash=T('please debug the application first (%(e)s)',dict(e=str(e)))
    redirect(URL(r=request,f='site'))

def remove_compiled_app():
    """ admin controller function """
    app=request.args[0]
    remove_compiled_application(apath(app))
    session.flash=T('compiled application removed')
    redirect(URL(r=request,f='site'))

def delete():
    """ admin controller function """
    filename='/'.join(request.args)
    sender=request.vars.sender
    try:
        if not request.vars.has_key('delete'): return dict(filename=filename,sender=sender)
        elif request.vars['delete']!='YES':
             session.flash=T('file "%(filename)s" was not deleted',dict(filename=filename))
             redirect(URL(r=request,f=sender))
        os.unlink(apath(filename))
        session.flash=T('file "%(filename)s" deleted',dict(filename=filename))
    except:
        session.flash=T('unable to delete file "%(filename)s"',dict(filename=filename))
    redirect(URL(r=request,f=sender))

def peek():
    """ admin controller function """
    filename='/'.join(request.args)
    try:
        data=open(apath(filename),'r').read()
    except IOError: 
        session.flash=T('file does not exist')
        redirect(URL(r=request,f='site'))
    extension=filename[filename.rfind('.')+1:].lower()    
    return dict(app=request.args[0],filename=filename,data=data,extension=extension)

def test():
    app=request.args[0]
    if len(request.args)>1: file=request.args[1]
    else: file='.*\.py'
    controllers=listdir(apath('%s/controllers/' % app), file + '$')
    return dict(app=app,controllers=controllers)

def edit():
    """ admin controller function """
    filename='/'.join(request.args)    
    if filename[-3:]=='.py': filetype='python'
    elif filename[-5:]=='.html': filetype='html'
    elif filename[-4:]=='.css': filetype='css'
    elif filename[-3:]=='.js': filetype='js'
    else: filetype='text'
    ### check if file is not there 
    data=open(apath(filename),'r').read()
    try:
        data=request.vars.data.replace('\r\n','\n').strip()
        open(apath(filename),'w').write(data)
        response.flash=T("file saved on %(time)s",dict(time=time.ctime()))       
    except: pass
    return dict(app=request.args[0],filename=filename,filetype=filetype,data=data)


def edit_language():
    """ admin controller function """
    filename='/'.join(request.args)    
    ### check if file is not there 
    strings=eval(open(apath(filename),'r').read())
    keys=strings.keys()
    keys.sort()
    rows=[]
    rows.append(TR(B(T('Original')),B(T('Translation'))))
    for keyi in range(len(keys)):
        key=keys[keyi]
        if len(key)<=40:
            rows.append(TR(key+' ',INPUT(_type='text',_name=str(keyi),value=strings[key],_size=40)))
        else:
            rows.append(TR(key+':',TEXTAREA(_name=str(keyi),value=strings[key],_cols=40,_rows=5)))
    rows.append(TR('',INPUT(_type='submit',_value='update')))
    form=FORM(TABLE(*rows))
    if form.accepts(request.vars,keepvalues=True):
        txt='{\n'
        for keyi in range(len(keys)):
            key=keys[keyi]
            txt+='%s:%s,\n' % (repr(key),repr(form.vars[str(keyi)]))
        txt+='}\n'
        open(apath(filename),'w').write(txt)        
        response.flash=T("file saved on %(time)s",dict(time=time.ctime()))       
    return dict(app=request.args[0],filename=filename,form=form)

def htmledit():
    """ admin controller function """
    filename='/'.join(request.args)    
    ### check if file is not there 
    data=open(apath(filename),'r').read()
    try:
        data=request.vars.data.replace('\r\n','\n') 
        open(apath(filename),'w').write(data)
        response.flash=T("file saved on %(time)s",dict(time=time.ctime()))       
    except: pass
    return dict(app=request.args[0],filename=filename,data=data)

def about():
    """ admin controller function """
    app=request.args[0] 
    ### check if file is not there 
    about=open(apath('%s/ABOUT' % app),'r').read()
    license=open(apath('%s/LICENSE' % app),'r').read()
    return dict(app=app,about=WIKI(about),license=WIKI(license))

def design():
    """ admin controller function """
    app=request.args[0] 
    if not response.slash and app==request.application:
        response.flash=T('ATTENTION: you cannot edit the running application!')
    if os.path.exists(apath('%s/compiled' % app)):
        session.flash=T('application is compiled and cannot be designed')
        redirect(URL(r=request,f='site'))
    models=listdir(apath('%s/models/' % app), '.*\.py$')
    defines={}
    for m in models:
        data=open(apath('%s/models/%s'%(app,m)),'r').read()
        defines[m]=regex_tables.findall(data)
        defines[m].sort()
    controllers=listdir(apath('%s/controllers/' % app), '.*\.py$')
    controllers.sort()
    functions={}    
    for c in controllers:
        data=open(apath('%s/controllers/%s' % (app,c)),'r').read()
        items=regex_expose.findall(data)
        functions[c]=items
    views=listdir(apath('%s/views/' % app),'.*\.html$')
    views.sort()
    extend={}
    include={}
    for c in views:
        data=open(apath('%s/views/%s' % (app,c)),'r').read()
        items=regex_extend.findall(data)
        if items: extend[c]=items[0][1]
        items=regex_include.findall(data)
        include[c]=[i[1] for i in items]
    statics=listdir(apath('%s/static/' % app),'[^\.#].*')
    statics.sort()
    languages=listdir(apath('%s/languages/' % app), '[\w-]*\.py')
    return dict(app=app,models=models,defines=defines,controllers=controllers,functions=functions,views=views,extend=extend,include=include,statics=statics,languages=languages)


def create_file():
    """ admin controller function """
    try:
        path=apath(request.vars.location)
        filename=re.sub('[^\w./-]+','_',request.vars.filename)        
        if path[-11:]=='/languages/':
            if len(filename)==0: raise SyntaxError
            app=path.split('/')[-3] 
            findT(apath(app),filename)
            session.flash=T('language file "%(filename)s" created/updated',dict(filename=filename))
            redirect(request.vars.sender)
        elif path[-8:]=='/models/': 
            if not filename[-3:]=='.py': filename+='.py'
            if len(filename)==3: raise SyntaxError
            fn=re.sub('\W','',filename[:-3].lower())
            text='# %s\n%s=SQLDB("sqlite://%s.db")' % (T('try something like'),fn,fn)
        elif path[-13:]=='/controllers/':
            if not filename[-3:]=='.py': filename+='.py'
            if len(filename)==3: raise SyntaxError
            text='# %s\ndef index(): return dict(message="hello from %s")' % (T('try something like'),filename)
        elif path[-7:]=='/views/':
            if not filename[-5:]=='.html': filename+='.html'
            if len(filename)==5: raise SyntaxError
            text="{{extend 'layout.html'}}\n<h1>%s</h1>\n{{=BEAUTIFY(response._vars)}}" % \
                 T('This is the %(filename)s template',dict(filename=filename))
        elif path[-8:]=='/static/':
            text=""
        else:
            redirect(request.vars.sender)
        filename=os.path.join(path,filename)
        dirpath=os.path.dirname(filename)
        if not os.path.exists(dirpath): os.makedirs(dirpath)
        if os.path.exists(filename): raise SyntaxError
        open(filename,'w').write(text)
        session.flash=T('file "%(filename)s" created',dict(filename=filename[len(path):]))
    except Exception, e:
        session.flash=T('cannot create file')
    redirect(request.vars.sender)

def upload_file(): 
    """ admin controller function """
    try:
        path=apath(request.vars.location)
        filename=re.sub('[^\w\./]+','_',request.vars.filename)
        if path[-8:]=='/models/' and not filename[-3:]=='.py': filename+='.py'
        if path[-13:]=='/controllers/' and not filename[-3:]=='.py': filename+='.py'
        if path[-7:]=='/views/' and not filename[-5:]=='.html': filename+='.html'
        if path[-11:]=='/languages/' and not filename[-3:]=='.py': filename+='.py'
        filename=os.path.join(path,filename)
        dirpath=os.path.dirname(filename)
        if not os.path.exists(dirpath): os.makedirs(dirpath)
        open(filename,'w').write(request.vars.file.file.read())
        session.flash=T('file "%(filename)s" uploaded',dict(filename=filename[len(path):]))
    except: 
        session.flash=T('cannot upload file "%(filename)s"',dict(filename[len(path):]))
    redirect(request.vars.sender)

def errors(): 
    """ admin controller function """
    app=request.args[0] 
    for item in request.vars:
        if item[:7]=='delete_':
            os.unlink(apath('%s/errors/%s' % (app,item[7:])))
    tickets=os.listdir(apath('%s/errors/' % app))
    return dict(app=app,tickets=tickets)

def ticket():        
    """ admin controller function """
    app=request.args[0] 
    ticket=request.args[1] 
    e=RestrictedError()
    e.load(apath('%s/errors/%s' % (app,ticket)))
    return dict(app=app,ticket=ticket,traceback=e.traceback,code=e.code,layer=e.layer)

def update_languages():
    """ admin controller function """
    app=request.args[0]
    update_all_languages(apath(app))
    session.flash=T('languages updated')
    redirect(URL(r=request,f='design/'+app))
