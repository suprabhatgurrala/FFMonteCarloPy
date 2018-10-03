class URLError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
    def __str__(self):
    	return 'URL Error: ' + super().__str__()

class IDError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
    def __str__(self):
    	return 'ID Error: ' + super().__str__()



class SimulatorError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
    def __str__(self):
    	return 'Simulator Error: ' + super().__str__()