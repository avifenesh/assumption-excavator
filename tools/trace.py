import sys,json
f=sys.argv[1]
mode=sys.argv[2] if len(sys.argv)>2 else "full"
for line in open(f):
    try: o=json.loads(line)
    except: continue
    t=o.get('type')
    if t=='assistant':
        for b in o.get('message',{}).get('content',[]):
            bt=b.get('type')
            if bt=='text': sys.stdout.write(b['text'])
            elif bt=='tool_use':
                n=b.get('name'); inp=b.get('input',{})
                if n=='Bash': sys.stdout.write('\n[BASH] '+str(inp.get('command',''))[:220]+'\n')
                elif n in ('WebSearch',): sys.stdout.write('\n[SEARCH] '+str(inp.get('query',''))[:160]+'\n')
                elif n in ('WebFetch',): sys.stdout.write('\n[FETCH] '+str(inp.get('url',''))[:160]+'\n')
                else: sys.stdout.write('\n['+str(n)+']\n')
    elif t=='user' and mode=='full':
        c=o.get('message',{}).get('content')
        if isinstance(c,list):
            for b in c:
                if b.get('type')=='tool_result':
                    r=b.get('content','')
                    if isinstance(r,list): r=' '.join(x.get('text','') for x in r if isinstance(x,dict))
                    sys.stdout.write('[RESULT] '+str(r)[:300]+'\n')
    elif t=='result':
        sys.stdout.write('\n=== '+str(o.get('subtype'))+' cost=$'+str(round(o.get('total_cost_usd',0),3))+' turns='+str(o.get('num_turns'))+' ===\n')
