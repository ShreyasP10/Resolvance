import re

with open('frontend/static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

old_try = """    try{
      const r=await fetch('/api/infer',{method:'POST',body:fd});
      clearInterval(iv); showProgress(true,100);
      const text=await r.text();
      try{ j=JSON.parse(text); }catch(e){ throw new Error(`Server ${r.status}: ${text.slice(0,400)}`); }"""

new_try = """    try{
      let r=await fetch('/api/infer',{method:'POST',body:fd});
      let text=await r.text();
      try{ j=JSON.parse(text); }catch(e){ throw new Error(`Server ${r.status}: ${text.slice(0,400)}`); }
      
      if(r.status === 202 && j.job_id) {
          // Poll for status
          const jobId = j.job_id;
          while(true) {
              await new Promise(res => setTimeout(res, 3000));
              let statusRes = await fetch(`/api/status/${jobId}`);
              let statusText = await statusRes.text();
              let statusJson;
              try { statusJson = JSON.parse(statusText); } catch(e) { throw new Error(`Status ${statusRes.status}: ${statusText.slice(0,400)}`); }
              if (statusRes.status === 200) {
                  j = statusJson;
                  break;
              } else if (statusRes.status === 202) {
                  continue; // Still processing
              } else {
                  throw new Error(statusJson.error || `Error ${statusRes.status}`);
              }
          }
      }
      clearInterval(iv); showProgress(true,100);
      """

js = js.replace(old_try, new_try)

with open('frontend/static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Frontend polling loop added!")
