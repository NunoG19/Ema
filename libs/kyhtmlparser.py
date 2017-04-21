from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint


class kyCollector:
    Root = None
    Datas = []
       
    def __init__(self):
        self.parent = None

        self.check_tag = False
        self.check_attr = False
        self.grab_tag = False
        self.grab_attr = False
        self.grab_data = False
        self.end_tag = None

        self.triggers = []
        self.data = ""

    def add_trigger(self, trigger):
        if trigger.tag:
            self.check_tag = True
        if trigger.attrs:
            self.check_attr = True
        self.triggers.append(trigger)
        trigger.collector = self
        trigger.next_collector.parent = self

    def remove_trigger(self, trigger):
        self.triggers.remove(trigger)

    def find(self, tag, attrs):
        trigger = kyTrigger(tag, attrs)
        self.add_trigger(trigger)
        trigger.find_all = False
        return trigger.next_collector
    
    def findall(self, tag, attrs):
        trigger = kyTrigger(tag, attrs)
        self.add_trigger(trigger)
        return trigger.next_collector

    def find_tag(self, tag):
        return self.find(tag, {})
    
    def findall_tag(self, tag):
        return self.findall(tag, {})

    def find_attr(self, attrs):
        return self.find(None, attrs)
    
    def findall_attr(self, attrs):
        return self.findall(None, attrs)
    
    def gettag(self):
        self.grab_tag = True
        
    def gettext(self):
        self.grab_data = True
    
    def getall(self):
        self.grab_tag = True
        self.grab_data = True

    def get(self, attr):
        self.grab_attr = True

    def check(self, tag, attrs):
        found = None
        if self.check_tag:
            for trigger in self.triggers:
                #print trigger.get()
                if trigger.tag == tag:
                    if self.check_attr:
                        if self.have_attr(attrs, trigger.attrs):
                            found = trigger
                            break
                    else:
                        found = trigger
                        break
                
        elif self.check_attr:
            for trigger in self.triggers:
                if self.have_attr(attrs, trigger.attrs):
                    found = trigger
                    break

        return found

    def have_attr(self, attrs, t_attrs):
        for attr, value in attrs:
            if attr in t_attrs:
                if t_attrs[attr] is not None :
                    return value == t_attrs[attr]
                return True
        return False
        
    
    def collect_datas(self):
        if self.data:
            kyCollector.Datas.append(self.data)
        self.data = ""

class kyTrigger:
    def __init__(self, tag="", attrs={}):
        self.find_all = True
        self.collector = None
        self.next_collector = kyCollector()
        self.tag = tag
        self.attrs = attrs

    def get(self):
        return self.tag, self.attrs, self.collector

class KyHtmlParser(HTMLParser, kyCollector):
    
    def __init__(self, src):
        HTMLParser.__init__(self)
        kyCollector.__init__(self)
        if type(src) == type("str"):
            src = src.decode("utf-8")
        self.src = src.replace(unichr(160), " ")\
            .replace(unichr(35799), unichr(35799)+" ").strip() # CHS
        self.triggers = []
        self.collector = self
        kyCollector.Root = self
        self.temp_data = ""
        self.catched_data = []

    def parse(self):
        kyCollector.Datas = []
        self.feed(self.src)
        return kyCollector.Datas
    
    def handle_starttag(self, tag, attrs):
        found = self.collector.check(tag, attrs)
        
        if found:
            #print "Sta Tag", tag, attrs
            if not found.find_all:
                self.collector.remove_trigger(found)
                
            self.collector = found.next_collector
            self.collector.end_tag = tag

            if self.collector.grab_tag:
                map_attrs = {}
                for k,v in attrs:
                    map_attrs[k] = v
                self.collector.data = [tag, map_attrs, ""]
            
            
    def handle_endtag(self, tag):
        if (self.collector.end_tag is not None
            and self.collector.end_tag == tag):
                self.collector.collect_datas()
                self.collector = self.collector.parent
                

    def handle_data(self, data):
        if self.collector.grab_data:
            #print "Data     :", data.encode("utf-8")
            if isinstance(self.collector.data, (list)): 
                self.collector.data[-1] = self.collector.data[-1] + data
            else:
                self.collector.data = self.collector.data + data

    def handle_comment(self, data):
        pass
        #print "Comment  :", data

    def handle_entityref(self, name):
        c = unichr(name2codepoint[name])
        #print "Named ent:", c

    def handle_charref(self, name):
        if name.startswith('x'):
            c = unichr(int(name[1:], 16))
        else:
            c = unichr(int(name))
        #print "Num ent  :", c

    def handle_decl(self, data):
        pass
        #print "Decl     :", data
