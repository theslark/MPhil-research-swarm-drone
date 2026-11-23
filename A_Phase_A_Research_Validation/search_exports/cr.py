import json,sys,urllib.request,urllib.parse,time
UA={"User-Agent":"research-lit-check/1.0"}
def get(url):
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30))
        except Exception as e: time.sleep(2)
    return None
def search(q,rows=8,frm="2023-01-01"):
    u="https://api.crossref.org/works?"+urllib.parse.urlencode({"query.bibliographic":q,"rows":rows,"filter":f"from-pub-date:{frm},type:journal-article,type:proceedings-article","select":"DOI,title,container-title,issued,type,author,abstract"})
    d=get(u); return d["message"]["items"] if d else []
def fmt(it):
    a=it.get("author",[]); au=", ".join((x.get("family","")) for x in a[:4])+(" et al." if len(a)>4 else "")
    y=(it.get("issued",{}).get("date-parts") or [[None]])[0][0]
    return f"{y} | {it.get('type')} | {(it.get('title') or [''])[0][:120]} | {(it.get('container-title') or [''])[0][:60]} | {au} | {it['DOI']} | abs={'Y' if it.get('abstract') else 'N'}"
if __name__=="__main__":
    for q in sys.stdin.read().strip().split("\n"):
        print("## ",q)
        for it in search(q): print("  ",fmt(it))
