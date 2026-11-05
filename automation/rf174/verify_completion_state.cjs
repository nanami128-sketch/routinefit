const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=process.argv[2]||'completion644/staged_final/index.html';
const html=fs.readFileSync(source,'utf8');
const script=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)].map(x=>x[1]).find(x=>x.includes('const VERSION='));
assert(script);
const prefix=script.slice(script.indexOf('const VERSION='),script.indexOf('const iconPaths='));
const persistence=script.slice(script.indexOf('const localISO='),script.indexOf('let installPromptEvent='));
const clean=script.slice(script.indexOf('function cleanBackup('),script.indexOf('function importBackup('));
const download=script.slice(script.indexOf('function backupDownload('),script.indexOf('function seedDemo('));
const iso='2026-11-03T08:00:00.000Z', id='ex12-e7a63bd979e32';
const sample={version:'1.7.4.3',revision:31,routines:{0:[{exerciseId:id,targetSets:4,restSec:120}]},sessions:[{id:'old-session',day:0,startedAt:iso,endedAt:iso,entries:[{exerciseId:'barbell-bench',sets:[{id:'old-set',weight:60,reps:10,createdAt:iso}]},{exerciseId:id,sets:[{id:'scapular-set',reps:12,createdAt:iso}]}]}],weights:[{date:'2026-11-03',weight:72.5,fat:18,muscle:33}],foods:[{id:'food-1',date:'2026-11-03',at:'2026-11-03T12:00:00',name:'식사',kcal:550,grams:300}],customExercises:[{id:'user-myexercise',name:'내 운동',muscle:'하체',equipment:'dumbbell',type:'weight',description:'사용자 설명',tip:'사용자 메모'}],exerciseOverrides:{'barbell-bench':{name:'내 벤치',description:'개인 메모',tip:'천천히'}},active:{id:'active-1',day:0,startedAt:iso,routineSnapshot:[{exerciseId:id,targetSets:3,restSec:60}],entries:[{exerciseId:id,sets:[{id:'active-set',reps:7,createdAt:iso}]}],currentExerciseIndex:0},settings:{goalWeight:70,sound:false,vibration:false,countdown:false,keepAwake:true}};
function boot(current,snapshot){
 const data=new Map();if(current!==undefined)data.set('routinefit_v1_store',current);if(snapshot!==undefined)data.set('routinefit_v13_snapshot',snapshot);
 let exported;
 const ctx=vm.createContext({console:{...console,warn:()=>{}},URL,Date,Math,Set,Map,JSON,Number,String,Boolean,Promise,localStorage:{getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v)},window:{RoutineFitNative:{saveBackup:s=>exported=s}},notify:()=>{}});
 vm.runInContext(prefix+persistence+clean+download+'\nglobalThis.test={getState:()=>state,cleanBackup,backupDownload,save,EXERCISES,byId,VERSION};',ctx);
 return {t:ctx.test,data,getExport:()=>exported};
}
const raw=JSON.stringify(sample), b=boot(raw);
assert.equal(b.t.EXERCISES.length,644);
assert.equal(new Set(b.t.EXERCISES.map(e=>e.id)).size,644);
assert.equal(b.t.getState().sessions[0].entries[0].sets[0].weight,60);
assert.equal(b.t.getState().active.entries[0].exerciseId,id);
b.t.backupDownload();const exported=JSON.parse(b.getExport());
assert.equal(exported.product,'RoutineFit');assert.equal(exported.exportVersion,b.t.VERSION);
const restored=b.t.cleanBackup(exported.data);
for(const field of ['sessions','weights','foods','customExercises','active','exerciseOverrides'])assert.ok(restored[field],field);
assert.equal(restored.sessions[0].entries.length,2);
assert.equal(restored.sessions[0].entries[1].exerciseId,id);
assert.equal(restored.sessions[0].entries[1].sets[0].reps,12);
assert.equal(restored.weights[0].weight,72.5);assert.equal(restored.foods[0].kcal,550);
assert.equal(restored.active.entries[0].sets[0].reps,7);
assert.equal(restored.routines[0][0].exerciseId,id);
assert.equal(restored.customExercises[0].name,'내 운동');
assert.equal(restored.exerciseOverrides['barbell-bench'].description,'개인 메모');
assert.equal(restored.settings.sound,false);assert.equal(restored.settings.countdown,false);
b.t.save();const saved=JSON.parse(b.data.get('routinefit_v1_store'));
assert.equal(saved.version,b.t.VERSION);assert.equal(saved.revision,32);
assert.equal(saved.sessions[0].id,'old-session');assert.equal(saved.active.id,'active-1');
assert.equal(JSON.parse(b.data.get('routinefit_v13_snapshot')).revision,31);
for(const current of [undefined,'{damaged']){const recovered=boot(current,raw);assert.equal(recovered.t.getState().sessions[0].id,'old-session');}
assert.equal(b.t.EXERCISES.find(e=>e.id===id).id,id);
if(b.t.VERSION==='1.7.4.5'){assert.equal(b.t.EXERCISES.find(e=>e.id===id).name,'스캐풀라 푸시업');assert.ok(b.t.EXERCISES.find(e=>e.id===id).aliases.includes('스캡션 푸시업'));}
console.log(JSON.stringify({source,version:b.t.VERSION,catalog:644,existing_records:'PASS',native_json_backup_roundtrip:'PASS',active_workout_and_routines:'PASS',custom_exercises_and_overrides:'PASS',save_revision_and_snapshot:'PASS',missing_or_corrupt_primary_snapshot_recovery:'PASS',scope:'Actual persistence and backup functions in Node VM; Android device and browser UI not tested.'}));
