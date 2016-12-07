from Common import *
import time

class Search(object):
    """
    search.onoff = 1
    search.type = 'EDGE'
    marks = search.mark_list
    marks = search.mark_on_screen
    total = len(search)
    search.copy_trigger('triggertosearch')
    config =  search.settings
    """
    def __init__(self, scope):
        self.scope = scope

    def _generate_cmd_list(self, source=''):
        cmd_list = {}
        if not source:
            source = self.scope << ':SEARCH:SEARCH1:TRIGGER:A:EDGE:SOURCE?'
        cmd_list['EDGE'] = {
            'source': ':SEARCH:SEARCH1:TRIGGER:A:EDGE:SOURCE',
            'slope': ':SEARCH:SEARCH1:TRIGGER:A:EDGE:SLOPE',
            'threshold': ':SEARCH:SEARCH1:TRIGGER:A:level:'+source
        }
        cmd_list['WIDTH'] = {
            'source': ':SEARCH:SEARCH1:TRIGGER:A:EDGE:SOURCE',
            'polarity': ':SEARCH:SEARCH1:TRIGGER:A:PULSEWIDTH:POLARITY',
            'when': ':SEARCH:SEARCH1:TRIGGER:A:PULSEWIDTH:WHEN',
            'width': ':SEARCH:SEARCH1:TRIGGER:A:PULSEWIDTH:WIDTH',
            'lowlimit': ':SEARCH:SEARCH1:TRIGGER:A:PULSEWIDTH:LOWLIMIT',
            'highlimit': ':SEARCH:SEARCH1:TRIGGER:A:PULSEWIDTH:HIGHLIMIT',
        }
        cmd_list['RUNT'] = {
            'source': ':SEARCH:SEARCH1:TRIGGER:A:EDGE:SOURCE',
            'polarity': ':SEARCH:SEARCH1:TRIGGER:A:RUNT:POLARITY',
            'when': ':SEARCH:SEARCH1:TRIGGER:A:RUNT:WHEN',
            'width': ':SEARCH:SEARCH1:TRIGGER:A:RUNT:WIDTH',
            'upperthreshold': ':SEARCH:SEARCH1:TRIGGER:A:UPPERTHRESHOLD:'+source,
            'lowerthreshold': ':SEARCH:SEARCH1:TRIGGER:A:lowerthreshold:'+source,
        }
        self.cmd_list = cmd_list

    def copy_trigger(self, direction):
        # {SEARCHtotrigger|TRIGgertosearch}
        self.scope << ':SEARCH:SEARCH1:COPY '+direction

    @property
    def onoff(self):
        return int(self.scope.Query(':SEARCH:SEARCH1:STATE?'))

    @onoff.setter
    def onoff(self, value):
        self.scope.Send(':SEARCH:SEARCH1:STATE ' + str(value))

    @property
    def type(self):
        mtype = self.scope.Query(':search:search1:trigger:A:type?')
        if mtype=='PULSEWIDTH':
            mtype = 'WIDTH'
        return mtype

    @type.setter
    def type(self, value):
        if value=='WIDTH':
            value = 'PULSEWIDTH'
        self.scope.Send(':search:search1:trigger:A:type '+value)

    @property
    def mark_list(self):
        ret = self.scope << 'search:search1:list?'
        if 'NONE' in ret:
            return []
        ret = ret.split(';')
        mark_list = []
        for i in ret:
            mark_list.append(i.split(','))
        return mark_list

    @property
    def mark_on_screen(self):
        half_hor_divs = self.scope.hor_divs/2.0
        hor_scale = self.scope.hor_scale
        range1, range2 = -hor_scale*half_hor_divs, hor_scale*half_hor_divs
        return [x for x in self.mark_list if float(x[4])<=range2 and float(x[4])>=range1]


    def __len__(self):
        return int(self.scope << ':search:search1:total?')

    @property
    def settings(self):
        self._generate_cmd_list()
        ret = {}
        type = self.type
        ret['type'] = type
        for key in self.cmd_list[type]:
            ret[key] = self.scope << self.cmd_list[type][key]+'?'
        return ret

    @settings.setter
    def settings(self, kargs):
        self._generate_cmd_list(kargs['source'])
        self.type = type = kargs.pop('type')
        for key in kargs:
            self.scope << self.cmd_list[type][key]+'  ' + str(kargs[key])



class Mark(object):
    """
    mark+1
    mark-1
    mark.create('CH1')
    mark.delete('CH1')
    mark.save()
    print(mark.user_list)
    len(mark)
    mark.source
    mark.owner
    mark.start
    mark.end
    mark.focus
    mark.marksincolumn
    mark.zoom_position
    """
    max = 1024

    def __init__(self, scope):
        self.scope = scope
        self.source_list = self.scope.InstInfo['channel_list'] + \
            self.scope.InstInfo['ref_list'] + ['MATH']

    def create(self, chan):
        self.scope << ':MARK:CREATE ' + chan

    def delete(self, chan):
        self.scope << ':MARK:DELETE ' + chan

    def clear_all(self):
        '''clear all marks'''
        self.scope.defaultsetup()
        self.scope.save_waveform('CH1', 'REF1')
        self.scope.save_waveform('CH1', 'REF2')
        assertEqual(0, len(self))

    def save(self):
        self.scope << 'MARK:SAVEALL TOUSER'

    def __add__(self, other):
        for i in range(other):
            self.scope.Send(':MARK NEXT')
            time.sleep(0.2)

    def __sub__(self, other):
        for i in range(other):
            self.scope.Send(':MARK PREVious')
            time.sleep(0.2)

    def __len__(self):
        return int(self.scope << ':MARK:TOTal?')

    @property
    def user_list(self):
        ret = self.scope << ':MARK:userlist?'
        if 'NONE' in ret:
            return []
        ret = ret.split(';')
        mark_list = []
        for i in ret:
            mark_list.append(i.split(','))
        return mark_list

    def __getattr__(self, item):
        # print('enter mark getattr ' + item)
        if item in ['end', 'start', 'marksincolumn',
            'focus', 'owner', 'source', 'state', 'zoom_position']:
            return self.scope << 'MARK:SELected:'+item.replace('_', ':')+'?'
        return None
