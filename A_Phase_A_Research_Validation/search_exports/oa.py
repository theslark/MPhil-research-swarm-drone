import json,sys,urllib.request,urllib.parse
ds=[l.strip() for l in open(sys.argv[1]) if l.strip()]
out={}
for i in range(0,len(ds),40):
    f="doi:"+"|".join(ds[i:i+40])
    u="https://api.openalex.org/works?"+urllib.parse.urlencode({"filter":f,"per-page":50,"select":"doi,title,publication_year,type,primary_location,authorships,abstract_inverted_index,biblio"})
    d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"research-lit-check/1.0"}),timeout=60))
    for r in d["results"]:
        inv=r.get("abstract_inverted_index") or {}
        pos=sorted((p,w) for w,ps in inv.items() for p in ps)
        r["abstract"]=" ".join(w for _,w in pos); r.pop("abstract_inverted_index",None)
        out[r["doi"].lower().replace("https://doi.org/","")]=r
json.dump(out,open("oa.json","w"),indent=1)
for k in ds:
    r=out.get(k.lower())
    if not r: print("MISSING",k); continue
    au=", ".join(a["author"]["display_name"] for a in r["authorships"][:6])
    src=((r.get("primary_location") or {}).get("source") or {}).get("display_name")
    b=r.get("biblio") or {}
    print(f"\n### {k} | {r['publication_year']} | {r['type']} | {src} | v{b.get('volume')} i{b.get('issue')} p{b.get('first_page')}-{b.get('last_page')}\nT: {r['title']}\nA: {au}{' et al.' if len(r['authorships'])>6 else ''}\nABS: {r['abstract'][:1400]}")
