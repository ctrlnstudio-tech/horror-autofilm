const state = {
  mode: "short",
  story: null,
  videoFileName: null,
  videos: [],
};

const places = [
  { title: "ห้องพักท้ายรีสอร์ต", visual: "old Thai resort room at the end of a narrow walkway" },
  { title: "คลินิกกะดึก", visual: "closed Thai night clinic with empty waiting chairs" },
  { title: "ตู้โทรศัพท์หน้าวัด", visual: "abandoned public phone booth in front of a Thai temple at night" },
  { title: "แพปลายเขื่อน", visual: "isolated floating raft house on a quiet dam lake" },
  { title: "บ้านเช่าข้างทางรถไฟ", visual: "old rental house beside a railway track in Thailand" },
  { title: "ห้องเก็บแฟ้มเทศบาล", visual: "municipal archive room filled with dusty case files" },
  { title: "โรงหนังปิดตาย", visual: "abandoned single-screen cinema with torn red seats" },
  { title: "ลิฟต์โรงพยาบาล", visual: "old hospital elevator with flickering floor numbers" },
  { title: "ศาลารอรถกลางนา", visual: "rural bus shelter surrounded by empty rice fields" },
  { title: "ห้องซ้อมดนตรีชั้นใต้ดิน", visual: "basement rehearsal room with old instruments" },
  { title: "ร้านถ่ายรูปโบราณ", visual: "old Thai photo studio with faded portraits" },
  { title: "บ้านพักครูหลังสุดท้าย", visual: "remote teacher housing behind a rural school" },
  { title: "ห้องผ่าศพเก่า", visual: "unused forensic room in an old hospital building" },
  { title: "โกดังของหาย", visual: "warehouse of lost belongings behind a bus station" },
  { title: "หอพักหญิงชั้นสี่", visual: "fourth floor corridor of an old women's dormitory" },
  { title: "ป้อมยามหมู่บ้านร้าง", visual: "security booth at the entrance of an abandoned housing estate" },
  { title: "ท่าเรือหลังตลาด", visual: "quiet pier behind a closed Thai market" },
  { title: "ห้องฉายภาพวงจรปิด", visual: "CCTV monitor room with many blank screens" },
  { title: "โรงงานน้ำแข็งเก่า", visual: "old ice factory with wet concrete floor" },
  { title: "บ้านไม้ริมคลอง", visual: "old wooden canal house in Thailand" },
  { title: "ห้องเช่าเหนือร้านยา", visual: "rental room above an old pharmacy" },
  { title: "สำนักงานทนายร้าง", visual: "abandoned lawyer office with legal folders" },
  { title: "สถานีอนามัยปิดปรับปรุง", visual: "closed rural health station at night" },
  { title: "ทางเดินหลังโรงแรม", visual: "service corridor behind an old Thai hotel" },
  { title: "ห้องเก็บชุดไทย", visual: "storage room full of old Thai traditional costumes" },
  { title: "ร้านวิดีโอเก่า", visual: "old Thai video rental store with VHS shelves" },
  { title: "ตึกแถวหลังตลาดสด", visual: "old shophouse behind a fresh market after closing" },
  { title: "บันไดหนีไฟชั้นสิบสาม", visual: "fire escape stairwell on the thirteenth floor" },
  { title: "ห้องพระในบ้านร้าง", visual: "abandoned prayer room with old altar and dust" },
  { title: "อู่รถกลางซอยลึก", visual: "empty car repair garage in a narrow alley" },
];

const protagonists = [
  "พนักงานต้อนรับกะดึก",
  "ไรเดอร์ส่งของ",
  "นักศึกษาฝึกงาน",
  "ช่างซ่อมกล้องวงจรปิด",
  "พยาบาลเวรดึก",
  "คนขับรถตู้",
  "แม่บ้านโรงแรม",
  "พนักงานเก็บเอกสาร",
  "เจ้าของร้านถ่ายรูป",
  "ครูบรรจุใหม่",
  "นักจัดรายการวิทยุท้องถิ่น",
  "เจ้าหน้าที่กู้ภัย",
  "คนดูแลหอพัก",
  "ยามหมู่บ้าน",
  "พนักงานร้านยา",
  "ช่างไฟของเทศบาล",
  "คนเฝ้าโกดัง",
  "เจ้าหน้าที่เวชระเบียน",
  "คนขับเรือรับจ้าง",
  "พนักงานโรงหนังเก่า",
];

const objects = [
  "กุญแจที่ไม่มีหมายเลข",
  "เทปวิดีโอที่ถูกเขียนว่าอย่ากรอกลับ",
  "รูปถ่ายที่มีเงาเพิ่มขึ้นทุกครั้ง",
  "โทรศัพท์บ้านที่ยังดังแม้ถูกตัดสาย",
  "สมุดลงชื่อที่มีชื่อคนตาย",
  "กล่องยาเก่าที่มีฉลากถูกขูดออก",
  "ตุ๊กตาผ้าซีดๆ ที่มีเข็มกลัดโรงแรม",
  "แฟ้มคดีที่หน้าสุดท้ายหายไป",
  "พวงกุญแจที่มีกลิ่นธูปติดอยู่",
  "นาฬิกาแขวนที่เดินถอยหลัง",
  "ซองจดหมายไม่มีผู้ส่ง",
  "เทียนสีดำที่ไม่มีวันดับ",
  "ตลับเทปเสียงของคนที่หายตัวไป",
  "บัตรคิวที่ออกเป็นเลขเดิมทุกครั้ง",
  "ผ้าคลุมเตียงที่ยังเปียกเหมือนเพิ่งซัก",
];

const ghosts = [
  "ผู้หญิงผมเปียกที่พูดด้วยเสียงของคนรู้จัก",
  "ชายแก่ที่เห็นได้เฉพาะในกระจก",
  "เงาคนไข้ที่ลากสายน้ำเกลือไปตามพื้น",
  "ผู้ฝึกงานที่ไม่มีชื่อในทะเบียน",
  "เจ้าของห้องคนเก่าที่ไม่ยอมออกไป",
  "แม่ชีเงียบๆ ที่ยืนอยู่ตรงบันได",
  "คนขายตั๋วที่ตายก่อนโรงหนังปิด",
  "เสียงผู้ชายที่อยู่ในลำโพงแต่ไม่มีตัว",
  "หญิงใส่ชุดไทยที่หันหลังตลอดเวลา",
  "ร่างดำที่ก้มอยู่ใต้โต๊ะทำงาน",
  "เงาคนเฝ้าศพที่เดินตามเสียงกุญแจ",
  "ผู้โดยสารที่ลงรถไปแล้วแต่ยังนั่งอยู่เบาะหลัง",
];

const events = [
  "ไฟทั้งชั้นดับพร้อมกัน แต่มีห้องเดียวที่ยังสว่าง",
  "กล้องวงจรปิดย้อนหลังไปเห็นเหตุการณ์ที่ยังไม่เกิด",
  "ประตูล็อกจากด้านใน ทั้งที่ไม่มีใครอยู่ในห้อง",
  "เสียงเคาะดังมาจากผนังแทนที่จะดังจากประตู",
  "ชื่อของตัวเอกไปปรากฏในสมุดลงชื่อเมื่อสิบปีก่อน",
  "โทรศัพท์โทรเข้ามาจากเบอร์ของสถานที่เดียวกัน",
  "ทุกคนจำเรื่องเดียวกันได้ไม่เหมือนกัน",
  "รูปถ่ายล่าสุดมีคนที่ไม่มีใครเห็นยืนอยู่กลางภาพ",
  "ลิฟต์ขึ้นไปชั้นที่ไม่มีอยู่จริง",
  "ของต้องห้ามย้ายตำแหน่งเองทุกครั้งที่หันหลัง",
  "เสียงประกาศเรียกชื่อคนที่ไม่ได้อยู่ในตึก",
  "พื้นเปียกเป็นรอยเท้าจากมุมห้องไปถึงเตียง",
];

const twists = [
  "สุดท้ายพบว่าสถานที่นั้นปิดตายมาตั้งแต่ก่อนวันที่ตัวเอกจำได้",
  "ชื่อผู้แจ้งเหตุคนแรกคือชื่อเดียวกับตัวเอก",
  "ภาพวงจรปิดเผยว่าตัวเอกเดินเข้าไปคนเดียว แต่ตอนออกมามีใครบางคนเดินตามหลัง",
  "คนที่เล่าเรื่องนี้ไม่ใช่ผู้รอดชีวิต แต่เป็นคนที่ยังติดอยู่ในสถานที่นั้น",
  "ของต้องห้ามไม่ได้ถูกเก็บไว้เพื่อกันคนเข้า แต่เพื่อกันบางอย่างไม่ให้ออกมา",
  "เสียงที่คอยเตือนมาตลอดคือเสียงของตัวเอกจากคืนสุดท้าย",
  "ห้องนั้นไม่เคยต้องการเหยื่อใหม่ มันต้องการให้คนจำเรื่องเดิมซ้ำๆ",
  "พอทุกอย่างจบ ตัวเอกพบว่าตัวเองกลายเป็นชื่อถัดไปในแฟ้มคดี",
];

const sceneBeats = [
  "เปิดด้วยสถานที่ต้องห้ามและวัตถุสำคัญ",
  "แนะนำตัวเอกและเหตุผลที่ต้องเข้าไป",
  "สัญญาณผิดปกติแรก",
  "ตัวเอกพยายามหาเหตุผลปกติ",
  "วัตถุต้องห้ามเริ่มตอบสนอง",
  "เสียงหรือเงาปรากฏชัดขึ้น",
  "ตัวเอกพบเบาะแสจากอดีต",
  "เหตุการณ์บังคับให้หนีไม่ได้",
  "ความจริงเริ่มย้อนกลับมาหาตัวเอก",
  "เฉลยจุดหักมุมและปิดเรื่อง",
];

const longExtraBeats = [
  "ย้อนประวัติสถานที่จากคนท้องถิ่น",
  "พบพยานคนแรกที่เล่าไม่หมด",
  "ตัวเอกกลับไปตรวจวัตถุอีกครั้ง",
  "มีคนโทรมาเตือนแต่สายขาด",
  "เอกสารเก่าขัดแย้งกับสิ่งที่ทุกคนรู้",
  "ตัวละครรองหายไปชั่วครู่",
  "กล้องหรือกระจกเผยสิ่งที่ตาเปล่าไม่เห็น",
  "ตัวเอกฝันถึงเหตุการณ์ในอดีต",
  "รอยเท้าหรือคราบน้ำพาไปยังจุดซ่อน",
  "ผีหลอกแบบไม่เห็นตัว แต่เปลี่ยนพื้นที่รอบตัว",
  "ตัวเอกเข้าใจผิดว่าออกจากสถานที่ได้แล้ว",
  "ความทรงจำของตัวเอกเริ่มไม่ตรงกับความจริง",
  "พบชื่อคนเกี่ยวข้องที่ไม่ควรอยู่ในปัจจุบัน",
  "วัตถุต้องห้ามเปิดเผยเสียงสุดท้าย",
  "ทางหนีทั้งหมดพากลับไปจุดเริ่มต้น",
  "ตัวเอกต้องเลือกว่าจะทำลายหรือเปิดของนั้น",
  "อดีตกับปัจจุบันทับกันในฉากเดียว",
  "ผีปรากฏเต็มตัวแบบไม่โจ่งแจ้ง",
  "ตัวเอกพบว่าตัวเองถูกเลือกตั้งแต่แรก",
  "ปิดด้วยภาพหรือเสียงที่บอกว่าเรื่องยังไม่จบในสถานที่นั้น",
];

function pick(list) {
  return list[Math.floor(Math.random() * list.length)];
}

function shuffle(list) {
  return [...list].sort(() => Math.random() - 0.5);
}

function buildSeed() {
  return {
    place: pick(places),
    protagonist: pick(protagonists),
    object: pick(objects),
    ghost: pick(ghosts),
    event: pick(events),
    twist: pick(twists),
  };
}

function lineForBeat(beat, seed, index, total) {
  const prefix = index === 0
    ? `ก่อนจะเล่าเรื่องนี้ ต้องบอกไว้ก่อนว่า "${seed.place.title}" ไม่ใช่สถานที่ที่คนแถวนั้นชอบพูดถึงหลังเที่ยงคืน`
    : "";

  const lines = [
    `${prefix} เพราะมีเรื่องเล่าว่า ${seed.object} จะปรากฏขึ้นเองทุกครั้งที่มีคนใหม่เดินเข้าไปใกล้เกินไป`.trim(),
    `${seed.protagonist} เข้าไปที่นั่นเพราะคิดว่าเป็นงานธรรมดา แต่ตั้งแต่วินาทีแรก บรรยากาศรอบตัวก็เงียบผิดปกติจนได้ยินเสียงหายใจของตัวเอง`,
    `สิ่งแรกที่ผิดปกติคือ ${seed.event} และไม่มีใครในบริเวณนั้นยอมสบตาเมื่อถูกถามว่าเกิดอะไรขึ้น`,
    `ตัวเอกพยายามบอกตัวเองว่ามันคงเป็นแค่ระบบไฟเก่า หรือเสียงลมผ่านช่องผนัง แต่ยิ่งเดินลึกเข้าไป ทุกอย่างยิ่งเหมือนถูกจัดฉากไว้รอ`,
    `${seed.object} ถูกวางอยู่ตรงจุดที่ไม่ควรมีใครเข้าถึงได้ และมันเย็นจัดเหมือนเพิ่งถูกหยิบออกมาจากน้ำแข็ง`,
    `ตอนนั้นเอง ${seed.ghost} เริ่มปรากฏอยู่ตามเงาสะท้อน ไม่ได้เข้ามาใกล้ แต่ก็ไม่เคยหายไปจากสายตา`,
    `ตัวเอกเจอเบาะแสเก่าที่บอกว่าเหตุการณ์แบบเดียวกันเคยเกิดขึ้นมาก่อน และคนที่เกี่ยวข้องทุกคนต่างหายไปหลังจากพูดชื่อสถานที่นี้`,
    `ประตูทางออกกลับเปิดไปสู่ทางเดินเดิมซ้ำๆ เหมือนตึกทั้งตึกกำลังบังคับให้เดินกลับไปหา ${seed.object}`,
    `เมื่อทุกอย่างเริ่มชัด ตัวเอกเข้าใจว่าเรื่องนี้ไม่ได้เริ่มในคืนนี้ แต่มันเริ่มตั้งแต่วันที่ชื่อของเขาไปโผล่ในบันทึกเก่าโดยไม่มีใครอธิบายได้`,
    `${seed.twist} และหลังจากคืนนั้น ไม่มีใครกล้าแตะ ${seed.object} อีกเลย แม้มันจะยังถูกพบอยู่ที่เดิมในทุกเช้า`,
  ];

  if (index < lines.length) return lines[index];

  const middle = [
    `เสียงเบาๆ จากมุมห้องเรียกชื่อตัวเอกด้วยน้ำเสียงที่คุ้นเกินไป ทั้งที่ในนั้นไม่มีใครควรรู้จักเขา`,
    `ทุกครั้งที่ไฟกะพริบ เงาบนพื้นจะเพิ่มขึ้นหนึ่งเงา และเงาสุดท้ายดูเหมือนกำลังยืนชิดหลังตัวเอกมากขึ้นเรื่อยๆ`,
    `สมุดบันทึกเก่าเขียนเหตุการณ์ของคืนนี้ไว้ละเอียด ตั้งแต่ก่อนที่ตัวเอกจะมาถึง`,
    `ตัวเอกเริ่มได้ยินเสียงฝีเท้าซ้อนกับฝีเท้าตัวเอง เหมือนมีใครเดินตามจังหวะเดียวกันอยู่ตลอดเวลา`,
    `รูปถ่ายบนผนังค่อยๆ เปลี่ยนไปจนกลายเป็นภาพสถานที่เดียวกันในคืนนี้ แต่มีร่างของตัวเอกอยู่ในภาพแล้ว`,
    `เสียงกระซิบไม่ได้ดังขึ้น แต่มันชัดขึ้นจนแยกออกว่าเป็นคำเตือน ไม่ใช่คำขู่`,
    `โทรศัพท์สั่นขึ้นมาเอง หน้าจอไม่มีเบอร์ มีแต่ข้อความสั้นๆ ว่าอย่าหันกลับไป`,
    `ตัวเอกเผลอหลับไปเพียงไม่กี่วินาที แต่เมื่อลืมตาอีกครั้ง นาฬิกาทุกเรือนในห้องเดินผ่านไปหลายชั่วโมง`,
    `มีรอยเปียกยาวจากประตูไปถึงวัตถุต้องห้าม ทั้งที่พื้นก่อนหน้านั้นแห้งสนิท`,
    `ยิ่งเข้าใกล้ความจริง สถานที่ก็ยิ่งเหมือนมีชีวิต มันปิดไฟ เปิดประตู และซ่อนทางออกตามใจตัวเอง`,
  ];

  if (index === total - 1) return lines[9];
  return pick(middle);
}

function visualPrompt(scene, seed, mode) {
  const aspect = mode === "long" ? "16:9 cinematic horizontal frame" : "9:16 vertical short video frame";
  return [
    `${aspect}, Thai horror film still, ${seed.place.visual}.`,
    `Exact scene: ${scene.narration}`,
    `Main character: one adult Thai ${seed.protagonist}.`,
    `Important object: ${seed.object}.`,
    `Atmosphere: mysterious, tense, cinematic, readable details, no children, no text in image, no random extra people.`,
  ].join(" ");
}

function buildStory(mode, briefText) {
  const seed = buildSeed();
  const title = briefText && briefText.trim().startsWith("อย่าเปิด")
    ? briefText.trim().slice(0, 42)
    : `อย่าเปิด...${seed.place.title}`;
  const targetSeconds = mode === "long" ? 600 : 95;
  const count = mode === "long" ? 34 : 10;
  const beats = mode === "long"
    ? shuffle([...sceneBeats, ...longExtraBeats]).slice(0, count)
    : sceneBeats.slice(0, count);

  const scenes = beats.map((beat, index) => {
    const narration = lineForBeat(beat, seed, index, beats.length);
    const duration = Math.round(targetSeconds / count);
    return {
      number: index + 1,
      beat,
      duration,
      narration,
      visual: visualPrompt({ narration }, seed, mode),
    };
  });

  return {
    mode,
    title,
    targetSeconds,
    scenes,
    script: scenes.map((scene) => scene.narration).join("\n\n"),
  };
}

const modeButtons = [...document.querySelectorAll(".mode")];
const viewButtons = [...document.querySelectorAll(".view")];
const brief = document.getElementById("brief");
const generateVideoButton = document.getElementById("generateVideo");
const randomizeButton = document.getElementById("randomize");
const runState = document.getElementById("runState");
const storyTitle = document.getElementById("storyTitle");
const storyDuration = document.getElementById("storyDuration");
const sceneCount = document.getElementById("sceneCount");
const scriptOutput = document.getElementById("scriptOutput");
const sceneList = document.getElementById("sceneList");
const visualList = document.getElementById("visualList");
const renderText = document.getElementById("renderText");
const renderPercent = document.getElementById("renderPercent");
const progressBar = document.getElementById("progressBar");
const videoLink = document.getElementById("videoLink");
const downloadLink = document.getElementById("downloadLink");
const videoList = document.getElementById("videoList");

modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    modeButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    state.mode = button.dataset.mode;
  });
});

viewButtons.forEach((button) => {
  button.addEventListener("click", () => {
    viewButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.querySelectorAll(".view-panel").forEach((panel) => panel.classList.remove("active"));
    document.getElementById(`${button.dataset.view}View`).classList.add("active");
  });
});

function renderStory(story) {
  storyTitle.textContent = story.title;
  storyDuration.textContent = story.mode === "long" ? "6 นาที+" : "1-2 นาที";
  sceneCount.textContent = `${story.scenes.length} ฉาก`;
  scriptOutput.textContent = story.script;

  sceneList.innerHTML = story.scenes.map((scene) => `
    <article class="scene-card">
      <div class="scene-meta">
        <strong>Scene ${scene.number}</strong>
        <span>${scene.duration}s</span>
      </div>
      <p class="scene-beat">${scene.beat}</p>
      <p>${scene.narration}</p>
    </article>
  `).join("");

  visualList.innerHTML = story.scenes.map((scene) => `
    <article class="scene-card">
      <div class="scene-meta">
        <strong>Prompt ${scene.number}</strong>
        <span>${story.mode === "long" ? "16:9" : "9:16"}</span>
      </div>
      <p>${scene.visual}</p>
    </article>
  `).join("");
}

function generateStory(useBrief) {
  runState.textContent = "กำลังสุ่มเรื่อง";
  const story = buildStory(state.mode, useBrief ? brief.value.trim() : "");
  state.story = story;
  renderStory(story);
  runState.textContent = "สร้างสคริปแล้ว";
}

function setProgress(percent, text) {
  renderPercent.textContent = `${percent}%`;
  progressBar.style.width = `${percent}%`;
  renderText.textContent = text;
}

async function generateVideo() {
  state.videoFileName = null;
  state.videos = [];
  videoLink.classList.remove("ready");
  videoLink.removeAttribute("href");
  downloadLink.classList.remove("ready");
  downloadLink.removeAttribute("href");
  downloadLink.removeAttribute("download");
  videoList.innerHTML = "";
  setProgress(8, "กำลังสุ่มเรื่องผี");
  runState.textContent = "กำลังเรนเดอร์";
  generateVideoButton.disabled = true;
  randomizeButton.disabled = true;

  const progressTimer = window.setInterval(() => {
    const current = parseInt(renderPercent.textContent, 10) || 8;
    if (current < 88) {
      let text = "กำลังสร้างภาพ AI realistic";
      if (current >= 34) text = "กำลังทำเสียงเล่าและซับไตเติ้ล";
      if (current >= 58) text = "กำลังใส่เพลงหลอนและเอฟเฟค";
      if (current >= 74) text = "กำลังตัดต่อวิดีโอสุดท้าย";
      setProgress(current + 4, text);
    }
  }, 1800);

  try {
    const response = await fetch("/api/generate-video", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: state.mode,
        brief: brief.value.trim(),
        count: 2,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Render failed");
    }

    const result = await response.json();
    const videos = result.videos && result.videos.length ? result.videos : [result];
    state.videos = videos;
    state.story = videos[0].story;
    state.videoFileName = videos[0].fileName;
    renderStory(videos[0].story);
    setProgress(100, "เรนเดอร์เสร็จแล้ว");
    runState.textContent = `ได้วิดีโอแล้ว ${videos.length} เรื่อง`;
    videoLink.href = videos[0].videoUrl;
    videoLink.textContent = `เปิดวิดีโอเรื่องที่ 1: ${videos[0].fileName}`;
    videoLink.classList.add("ready");
    downloadLink.href = videos[0].downloadUrl || videos[0].videoUrl;
    downloadLink.download = videos[0].fileName;
    downloadLink.dataset.file = videos[0].fileName;
    downloadLink.textContent = `ดาวน์โหลดเรื่องที่ 1`;
    downloadLink.classList.add("ready");
    videoList.innerHTML = videos.map((video, index) => `
      <article class="video-item">
        <strong>เรื่องที่ ${index + 1}: ${video.story.title}</strong>
        <div class="video-item-actions">
          <a class="open-item" href="${video.videoUrl}" target="_blank" rel="noreferrer">เปิดดู</a>
          <a class="download-item" href="${video.downloadUrl || video.videoUrl}" data-file="${video.fileName}" download="${video.fileName}">ดาวน์โหลด</a>
        </div>
      </article>
    `).join("");
  } catch (error) {
    setProgress(0, `ตัดต่อไม่สำเร็จ: ${error.message}`);
    runState.textContent = "มีข้อผิดพลาด";
  } finally {
    window.clearInterval(progressTimer);
    generateVideoButton.disabled = false;
    randomizeButton.disabled = false;
  }
}

generateVideoButton.addEventListener("click", generateVideo);
randomizeButton.addEventListener("click", () => generateStory(false));

downloadLink.addEventListener("click", async (event) => {
  if (!state.videoFileName) return;
  event.preventDefault();
  await saveVideoFile(downloadLink, state.videoFileName);
});

videoList.addEventListener("click", async (event) => {
  const link = event.target.closest(".download-item");
  if (!link) return;
  event.preventDefault();
  await saveVideoFile(link, link.dataset.file);
});

async function saveVideoFile(link, fileName) {
  if (!fileName) return;
  const label = link.textContent;
  link.textContent = "กำลังบันทึก";
  try {
    const response = await fetch("/api/save-video", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fileName }),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Save failed");
    }
    const result = await response.json();
    link.textContent = `บันทึกแล้ว`;
    renderText.textContent = `บันทึกไฟล์ไว้ที่ ${result.savedPath}`;
  } catch (error) {
    link.textContent = label;
    renderText.textContent = `บันทึกไม่สำเร็จ: ${error.message}`;
    window.location.href = link.href;
  }
}
