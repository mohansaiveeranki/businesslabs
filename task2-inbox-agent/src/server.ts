import { createServer } from "node:http";
import { draft } from "./drafting/agent.ts";
import { recordFeedback } from "./feedback/store.ts";
import { categories, type Category } from "./email/types.ts";
const server=createServer(async(req,res)=>{
  const origin=req.headers.origin;
  if(origin==="http://127.0.0.1:8000"||origin==="http://localhost:8000") res.setHeader("access-control-allow-origin",origin);
  res.setHeader("vary","Origin"); res.setHeader("access-control-allow-headers","content-type"); res.setHeader("access-control-allow-methods","GET,POST,OPTIONS");
  if(req.method==="OPTIONS"){res.writeHead(204).end();return;}
  if(req.method==="GET"&&req.url==="/health"){res.writeHead(200,{"content-type":"application/json"}).end(JSON.stringify({status:"ok",service:"inbox-agent"}));return;}
  const chunks:Buffer[]=[]; let size=0; for await (const chunk of req) { const bytes=Buffer.from(chunk); size+=bytes.length; if(size>20000){res.writeHead(413).end(JSON.stringify({error:"Request body too large"}));return;} chunks.push(bytes); }
  try {
    const data=JSON.parse(Buffer.concat(chunks).toString("utf8")||"{}");
    if(req.method!=="POST") throw Object.assign(new Error("POST required"),{status:405});
    if(req.url==="/draft") { const result=await draft(data); res.writeHead(200,{"content-type":"application/json"}).end(JSON.stringify(result)); return; }
    if(req.url==="/feedback") { if(!categories.includes(data.category)||!["sent_unchanged","edited","rejected","unsafe"].includes(data.outcome)||typeof data.draftText!=="string"||typeof data.finalText!=="string") throw new Error("Invalid feedback event"); const result=await recordFeedback(data.category as Category,data.outcome,data.draftText,data.finalText); res.writeHead(200,{"content-type":"application/json"}).end(JSON.stringify(result)); return; }
    res.writeHead(404).end(JSON.stringify({error:"Not found"}));
  } catch(error) { const status=(error as {status?:number}).status??400; res.writeHead(status,{"content-type":"application/json"}).end(JSON.stringify({error:error instanceof Error?error.message:"Invalid request"})); }
});
server.listen(8001,"127.0.0.1",()=>console.log("Inbox Agent listening on http://127.0.0.1:8001"));
