// Actual Agentify code, frozen ACPS prompt, isolated state and mocked external effects.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
const [source, scratch, handoffPath] = process.argv.slice(2);
const load = name => import(pathToFileURL(path.join(source, name)).href);
const { ChatGPTController, classifyChatgptStrictProductSelection: classify } = await load('chatgpt-controller.mjs');
const { runReviewQuery } = await load('review-transport.mjs');
const { readReviewTransportState } = await load('state.mjs');
const { REVIEW_PLAIN_TEXT_MODEL, reviewPlainTextIdentity } = await load('review-text-identity.mjs');
const { REVIEW_COMPOSER_REPLACEMENT_MODEL } = await load('review-composer-replacement.mjs');
const handoff = JSON.parse(await fs.readFile(handoffPath, 'utf8'));
const prompt = handoff.transport_request.prompt;
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const hmasdQuestionKey = ({repository,branch,subject,sourceSha,targetPath,questionHeading}) =>
  `hmasd:${sha(JSON.stringify([repository,branch,subject,sourceSha,targetPath,questionHeading]))}`;
const questionIdentity = {
  repository:'firesurfer/HMASD', branch:'main', subject:'actuator_conditioned_partial_sharing',
  sourceSha:'aaf0b977de1f547794ac0a540480be9778f1524e',
  targetPath:'docs/research/candidates/actuator_conditioned_partial_sharing/NOTES.md',
  questionHeading:'2026-09-12 Pro question — post-B02 use'
};
const questionKey = hmasdQuestionKey(questionIdentity);
assert.match(questionKey,/^hmasd:[0-9a-f]{64}$/);
assert.equal(questionKey,hmasdQuestionKey({...questionIdentity}));
assert.equal(sha(prompt), 'bee9b6e037f7b68e37143d152dd004cfefd10a9904d5c13bb648750ee9a2ab84');
assert.equal(handoff.parent_thread_id, '/root/dm_acps_resume');
assert.equal(handoff.operator_thread_id, '/root/dm_acps_resume/transport_lh_acps');
assert.equal(handoff.provider_requirement.model, 'GPT-6 Astra');
const base = { requestedProductModel:'GPT-6 Astra', closedModelLabel:'6Pro', menuCount:1,
  records:[{label:'Latest',selected:true},{label:'GPT-5.6 Sol',selected:false},{label:'GPT-5.5',selected:false}] };
let checks = 0;
const expect = (args, matched) => { assert.equal(classify({...base,...args}).matched, matched); checks++; };
expect({}, true);
expect({closedModelLabel:'6 Pro'}, true);
expect({closedModelLabel:'7 Pro'}, false);
expect({closedModelLabel:'Pro'}, false);
expect({closedModelLabel:null}, false);
expect({closedModelLabel:'Account 6 Pro'}, false);
expect({menuCount:2}, false);
expect({records:[{label:'Latest',selected:false}]}, false);
expect({records:[{label:'Latest',selected:true},{label:'Latest',selected:true}]}, false);
expect({records:[{label:'Latest',selected:true},{label:'GPT-5.5',selected:true}]}, false);
expect({records:[{label:'Latest',selected:true},{label:'GPT-6 Astra',selected:false}]}, false);
expect({closedModelLabel:null, records:[{label:'GPT-6 Astra',selected:true}]}, true);
assert.equal(classify(base).requestedProductModel, 'GPT-6 Astra');
assert.equal(classify(base).matchedLabel, 'Latest');

// Execute the real non-sending preflight and its browser expressions against a
// small visible DOM fixture. Sidebar/account text never supplies the model cue.
function pageFixture(closedLabel='6Pro', powerLabel='Pro') {
  let open=false, pointerClicks=0, productReads=0, powerReads=0;
  const rect={x:610,y:670,width:80,height:36,left:610,right:690,top:670,bottom:706};
  const node=(label,attrs={})=>({textContent:label,getAttribute:k=>attrs[k]??null,
    getBoundingClientRect:()=>rect,closest:()=>null});
  const trigger=node(closedLabel), account=node('Account 6 Pro');
  const composer={contains:n=>n===trigger};
  const textbox={...node(''),closest:s=>s==='form'?composer:null,parentElement:null};
  const products=base.records.map(r=>node(r.label,{'aria-label':r.label,'aria-checked':String(r.selected)}));
  const owner=node('Power',{'aria-describedby':'power-description'});
  const slider=node('',{'aria-valuemin':'0','aria-valuemax':'4','aria-valuenow':'4'});
  const powerRoot={querySelectorAll:()=>[slider],closest:()=>owner};
  const menu={...node(''),querySelector:()=>({}),querySelectorAll:selector=>
    selector.includes('composer-model-picker-slider-advanced-view')?products:
    selector==='[data-model-reasoning-effort-slider]'?[powerRoot]:[]};
  const document={querySelectorAll:selector=>selector==='#prompt'?[textbox]:
    selector.startsWith('[role="menu"]')?(open?[menu]:[]):
    selector.startsWith('button[aria-haspopup')?[trigger,account]:[],
    getElementById:id=>id==='power-description'?{textContent:powerLabel}:null};
  const window={getComputedStyle:()=>({display:'block',visibility:'visible'})};
  const page={getUrl:async()=> 'https://chatgpt.com/',
    evaluate:async js=>{
      if(js.includes('agentifyFocusChatgptReasoningEffortOwnerMarker'))return {focused:false,ownerCount:0};
      if(js.includes('agentifyChatgptProductModelStateMarker'))productReads++;
      if(js.includes('agentifyChatgptReasoningSliderStateMarker'))powerReads++;
      assert.ok(/agentify(?:Open|Verify|Close|Chatgpt)/.test(js), 'Unexpected browser expression');
      return Function('document','window',`return ${js}`)(document,window);
    },moveMouse:async()=>{},mouseDown:async()=>{},mouseUp:async()=>{open=true;pointerClicks++;},
    sendKey:async key=>{assert.equal(key,'Escape');open=false;},
    insertText:async()=>{throw new Error('preflight inserted prompt');}};
  const controller=new ChatGPTController({page,selectors:{promptTextarea:'#prompt'}});
  controller.ensureReady=async()=>{}; // login readiness is outside this selector fixture
  return {controller, counts:()=>({pointerClicks,productReads,powerReads,open})};
}
const page=pageFixture();
const proof=await page.controller.reviewPreflight({productModel:'GPT-6 Astra',reasoningEffort:'Pro',timeoutMs:3000});
assert.equal(proof.productModelEvidence.matched,true);
assert.equal(proof.productModelEvidence.selectionMapping,'latest_with_composer_6_pro');
assert.equal(proof.productModelEvidence.closedModelLabel,'6Pro');
assert.equal(proof.reasoningEffortEvidence.matchedLabel,'Pro');
assert.equal(proof.promptInsertCount,0);
assert.deepEqual(page.counts(),{pointerClicks:1,productReads:1,powerReads:1,open:false});
const wrong=pageFixture('Pro');
await assert.rejects(wrong.controller.reviewPreflight({productModel:'GPT-6 Astra',reasoningEffort:'Pro'}),/product_model_unavailable/);
assert.equal(wrong.counts().powerReads,0);
const wrongPower=pageFixture('6Pro','High');
await assert.rejects(wrongPower.controller.reviewPreflight({productModel:'GPT-6 Astra',reasoningEffort:'Pro'}),/reasoning_effort_power_owner_unavailable/);

let sends=0;
const directories=[];
async function prepareVerifiedComposer(args, baselineMessageIds) {
  await args.onPrepared({baselineMessageIds});
  const canonicalPromptSha256=reviewPlainTextIdentity(args.prompt).canonicalSha256;
  await args.onComposerVerified({
    ok:true,
    textModel:REVIEW_PLAIN_TEXT_MODEL,
    replacementModel:REVIEW_COMPOSER_REPLACEMENT_MODEL,
    sourceSha256:sha(args.prompt),
    canonicalPromptSha256,
    observedCanonicalSha256:canonicalPromptSha256
  });
}
async function scenario(name, uncertain=false) {
  const stateDir=path.join(scratch,name); directories.push(stateDir);
  let repaired=uncertain;
  const request={stableKey:questionKey,provider:'chatgpt',productModel:'GPT-6 Astra',
    reasoningEffort:'Pro',conversationUrl:'https://chatgpt.com/',conversationId:'__new__',firstBinding:true,
    idempotencyKey:questionKey,prompt,promptSha256:sha(prompt),responsePath:path.join(stateDir,'response.md'),
    existingTabId:'fixture-existing-Q-tab',timeoutMs:1000};
  const identity={conversationUrl:'https://chatgpt.com/c/fixture-q',conversationId:'fixture-q',userMessageId:'fixture-user'};
  const response='Fixture complete response. No external effect.\n';
  const controller={runExclusive:async fn=>await fn(),reviewQuery:async args=>{
    assert.equal(args.productModel,'GPT-6 Astra'); assert.equal(args.reasoningEffort,'Pro');
    assert.equal(args.requireTargetPreflight,true);
    if(!repaired)throw new Error('chatgpt_product_model_unavailable_or_unselected');
    assert.equal(classify(base).matched,true);
    await prepareVerifiedComposer(args, []);
    await args.onSendAttempted(); sends++;
    if(uncertain)throw new Error('fixture_uncertain_effect');
    await args.onUserTurnObserved(identity); return identity;
  },observeReviewUserTurn:async()=>identity,observeReviewResponse:async()=>({...identity,assistantMessageId:'fixture-assistant',
    text:response,snapshots:[1000,4000].map(observedAt=>({assistantMessageId:'fixture-assistant',textSha256:sha(response),observedAt})),
    controls:{stop:false,continue:false,retry:false},clickedControls:[]})};
  const tabs={adoptTab:async args=>assert.equal(args.id,request.existingTabId),ensureTab:async()=>request.existingTabId,
    getWindowById:()=>({show:async()=>{}}),getControllerById:()=>controller,updateTabUrl:()=>{}};
  const run=next=>runReviewQuery({stateDir,tabs,request:next||request});
  const op=async()=> (await readReviewTransportState(stateDir)).operations[request.idempotencyKey];
  await assert.rejects(run(), uncertain?/fixture_uncertain_effect/:/product_model_unavailable/);
  const before=await op(); assert.equal(before.sendAttempted,uncertain);
  await assert.rejects(run({...request,productModel:'Latest'}),/idempotency_conflict/);
  const sendsBeforeRepair=sends;
  repaired=true;const after=await run({...request,verifyExisting:true});
  if(uncertain)assert.equal(sends,sendsBeforeRepair);
  assert.equal(after.operationId,before.operationId);
  assert.equal(after.requestFingerprint,before.requestFingerprint);
  assert.equal(after.productModel,'GPT-6 Astra');
  assert.equal(after.archive.sha256,sha(response));
  assert.equal(after.archive.sizeBytes,Buffer.byteLength(response));
  assert.equal(after.providerUserMessageId,'fixture-user');
  assert.equal(after.providerAssistantMessageId,'fixture-assistant');
  const sendsAtArchive=sends;await run({...request,verifyExisting:true});assert.equal(sends,sendsAtArchive);
}

async function conversationKeyScenario() {
  const stateDir=path.join(scratch,'conversation-key-migration'); directories.push(stateDir);
  let firstBindingNumber=0;
  const response='Fixture complete response. No external effect.\n';
  const controller={runExclusive:async fn=>await fn(),reviewQuery:async args=>{
    assert.equal(args.requireTargetPreflight,true);
    const identity=args.firstBinding
      ? {conversationUrl:`https://chatgpt.com/c/fixture-new-${++firstBindingNumber}`,conversationId:`fixture-new-${firstBindingNumber}`}
      : {conversationUrl:args.expectedUrl,conversationId:args.expectedConversationId};
    await prepareVerifiedComposer(args, args.firstBinding?[]:['fixture-existing-user']);
    await args.onSendAttempted(); sends++;
    await args.onUserTurnObserved({...identity,userMessageId:`fixture-user-${sends}`});
    return {...identity,userMessageId:`fixture-user-${sends}`};
  },observeReviewResponse:async args=>({conversationUrl:args.expectedUrl,conversationId:args.expectedConversationId,
    userMessageId:args.userMessageId,assistantMessageId:`fixture-assistant-${args.expectedConversationId}`,
    text:response,snapshots:[1000,4000].map(observedAt=>({assistantMessageId:`fixture-assistant-${args.expectedConversationId}`,
      textSha256:sha(response),observedAt})),controls:{stop:false,continue:false,retry:false},clickedControls:[]})};
  const tabs={adoptTab:async()=>{},ensureTab:async()=> 'fixture-existing-key-tab',
    getWindowById:()=>({show:async()=>{}}),getControllerById:()=>controller,updateTabUrl:()=>{}};
  const request=(stableKey,idempotencyKey,conversationId,{firstBinding=false,responseName}={})=>({
    stableKey,provider:'chatgpt',productModel:'GPT-6 Astra',reasoningEffort:'Pro',
    conversationUrl:firstBinding?'https://chatgpt.com/':`https://chatgpt.com/c/${conversationId}`,
    conversationId:firstBinding?'__new__':conversationId,firstBinding,idempotencyKey,prompt,promptSha256:sha(prompt),
    responsePath:path.join(stateDir,responseName),existingTabId:'fixture-existing-key-tab',timeoutMs:1000
  });

  const oldKey=handoff.conversation_binding_key;
  await runReviewQuery({stateDir,tabs,request:request(oldKey,handoff.request_id,'fixture-old-a',{responseName:'old-a.md'})});
  const beforeRejected=sends;
  await assert.rejects(runReviewQuery({stateDir,tabs,request:request(oldKey,`${handoff.request_id}-next`,
    'fixture-old-b',{responseName:'old-b-rejected.md'})}),/review_binding_mismatch/);
  assert.equal(sends,beforeRejected);

  const nextQuestionKey=hmasdQuestionKey({...questionIdentity,questionHeading:'2026-09-16 Pro question — next idea'});
  assert.notEqual(nextQuestionKey,questionKey);
  const existingConversation=await runReviewQuery({stateDir,tabs,request:request(nextQuestionKey,nextQuestionKey,
    'fixture-old-b',{responseName:'new-key-existing-conversation.md'})});
  assert.equal(existingConversation.stableKey,nextQuestionKey);
  assert.equal(existingConversation.idempotencyKey,nextQuestionKey);

  const freshQuestionKey=hmasdQuestionKey({...questionIdentity,questionHeading:'2026-09-16 Pro question — fresh conversation'});
  const freshConversation=await runReviewQuery({stateDir,tabs,request:request(freshQuestionKey,freshQuestionKey,
    '__new__',{firstBinding:true,responseName:'new-key-new-conversation.md'})});
  assert.equal(freshConversation.observedConversationId,'fixture-new-1');
  const state=await readReviewTransportState(stateDir);
  assert.equal(state.bindings[freshQuestionKey].conversationId,'fixture-new-1');
  assert.equal(sends,beforeRejected+2);
}
try {
  await scenario('verified-nonacceptance');assert.equal(sends,1);
  await scenario('uncertain-effect',true);assert.equal(sends,2);
  await conversationKeyScenario();assert.equal(sends,5);
  process.stdout.write(JSON.stringify({selector_cases:checks,real_preflight_fixture:true,
    frozen_handoff_sha_verified:true,same_operation_repair:true,latest_argument_conflict_preserved:true,
    uncertain_observe_only:true,same_question_key_recovery_zero_resend:true,archive_exact:true,
    old_key_different_conversation_rejected:true,new_question_key_existing_conversation:true,
    new_question_key_first_binding:true,mock_sends:sends,external_sends:0}));
} finally {
  for(const dir of directories) {
    const entries=await fs.readdir(dir);
    for(const entry of entries)assert.ok(entry==='review-transport.json'||entry.endsWith('.md'),entry);
    for(const entry of entries)await fs.unlink(path.join(dir,entry));
    await fs.rmdir(dir);
  }
}
