import { draft } from "./drafting/agent.ts";
const result=await draft({id:"DEMO-01",from:"client@example.com",subject:"Update our logo",body:"How do I update the logo on my site?"});
console.log(JSON.stringify(result,null,2));
