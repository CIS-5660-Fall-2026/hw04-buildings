"""Small helpers for constructing readable native Houdini networks."""
import hou

def node(parent,kind,name,inputs=(),values=None,comment=None):
    n=parent.createNode(kind,name)
    for i,src in enumerate(inputs):
        if src is not None:n.setInput(i,src)
    for k,v in (values or {}).items():
        p=n.parmTuple(k) if isinstance(v,(tuple,list)) else n.parm(k)
        if p is None:raise ValueError(n.path()+'/'+k)
        p.set(v)
    if comment:n.setComment(comment);n.setGenericFlag(hou.nodeFlag.DisplayComment,True)
    return n

def ex(n,p,s):n.parm(p).setExpression(s,hou.exprLanguage.Hscript)
def ref(n,target,p):return 'ch("'+n.relativePathTo(target)+'/'+p+'")'
def wr(parent,name,src,code,cls='primitive',extra=()):
    return node(parent,'attribwrangle',name,(src,)+tuple(extra),{'class':cls,'snippet':code})
def finish(parent,src,name='OUT'):
    n=node(parent,'null',name,(src,));n.setDisplayFlag(True);n.setRenderFlag(True)
    n.setColor(hou.Color((.25,.65,.4)));parent.layoutChildren();return n
def shade(parent,name,src,material,group):
    return wr(parent,name,src,'s@shop_materialpath="/mat/%s"; v@Cd=chv("/mat/%s/basecolor"); i@group_%s=1;'%(material,material,group))
def dbox(parent,name,size,pos=(0,0,0),bindings=None):
    n=node(parent,'box',name)
    refs={k:ref(n,*v) for k,v in (bindings or {}).items()}
    for prefix,vals in [('size',size),('t',pos)]:
        for axis,v in zip('xyz',vals):
            if isinstance(v,str):ex(n,prefix+axis,v.format_map(refs))
            else:n.parm(prefix+axis).set(v)
    return n
def asset_id(parent,src,i):
    n=wr(parent,'point_ID',src,f'i@ID={i};','point')
    return wr(parent,'primitive_ID',n,f'i@ID={i};')
def fparm(name,label,value,lo,hi):
    return hou.FloatParmTemplate(name,label,1,default_value=(value,),min=lo,max=hi,min_is_strict=True,max_is_strict=True)
def iparm(name,label,value,lo,hi):
    return hou.IntParmTemplate(name,label,1,default_value=(value,),min=lo,max=hi,min_is_strict=True,max_is_strict=True)
def aim(n,pos,target):
    n.parmTuple('t').set(pos)
    n.parmTuple('r').set(hou.hmath.buildRotateLookAt(hou.Vector3(pos),hou.Vector3(target),hou.Vector3(0,1,0)).extractRotates())
