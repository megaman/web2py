response.title="web2py Enterprise Web Framework"
response.keywords="web2py, Gluon, Python, Enterprise, Web, Framework"
response.description="web2py Enterprise Web Framework"

app=request.application
response.menu=[
  ['home',request.function=='index','/%s/default/index'%app],
  ['download',request.function=='download','/%s/default/download'%app],
  ['features',request.function=='features','/%s/default/features'%app],
  ['faq',request.function=='faq','/%s/default/faq'%app],
  ['api',request.function=='api','/%s/default/api'%app],
  ['orm',request.function=='orm','/%s/default/orm'%app],
  ['examples',request.function=='examples','/%s/default/examples'%app],
  ['license',request.function=='license','/%s/default/license'%app],
  ['thanks',request.function=='thanks','/%s/default/thanks'%app]]

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def index(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def download(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def examples(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def features(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def api(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def thanks(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def faq(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def license(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def orm(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def web2py_vs_php(): return response.render(dict())

@cache(request.env.path_info,time_expire=600,cache_model=cache.ram) 
def version(): return open('VERSION','r').read()