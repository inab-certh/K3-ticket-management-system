# records/forms/__init__.py
#from .person import PersonForm
#from .neoplasm import NeoplasmForm
#from .therapy import TherapyForm
#from .request import RequestForm
#from .action import ActionForm

#__all__ = ["PersonForm", "NeoplasmForm", "TherapyForm", "RequestForm"]

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if self.instance and self.instance.action_date:
        self.initial['action_date'] = self.instance.action_date.strftime('%Y-%m-%d')
    if self.instance and self.instance.follow_up_date:
        self.initial['follow_up_date'] = self.instance.follow_up_date.strftime('%Y-%m-%d')