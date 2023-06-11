const baseVideo = document.getElementById("base_video");
const overlayVideo = document.getElementById("overlay_video");
const outputPreview = document.getElementById("output-video-preview");
const basePreview = document.getElementById("base-video-preview");
const overlayPreview = document.getElementById("overlay-video-preview");
const colorInput = document.getElementById("overlay_color");

function wait(timeout) {
    return new Promise((res) => setTimeout(res, timeout));
}

async function run() {
  document.getElementById("app_start").style.display = "none";
  document.getElementById("app_pending").style.display = "";

  const form = new FormData();
  form.append("config", JSON.stringify({
      color: colorInput.value,
  }))
  form.append("base_video", baseVideo.files[0]);
  form.append("overlay_video", overlayVideo.files[0]);

  // Upload files
  const response = await fetch("/api/requests", {
      method: "PUT",
      body: form,
  });

  if(response.status === 429) {
    alert("Chill out, too many requests from your IP. Retry after 1 minute");
    return;
  }

  if(response.status !== 202) {
    alert('error');  
    return;
  }

  const { id } = await response.json();

  // Check status with timeout 2s
  let status = "queue";
  while(status === "queue" || status === "processing") {
      await wait(2000);
      const response = await fetch(`/api/requests/${id}`);
      const data = await response.json();
      status = data.status;

      console.log(status);
  }

  if(status === "ready") {
    // Show video on page
    document.getElementById("app_pending").style.display = "none";
    document.getElementById("app_result").style.display = "";

    const video = document.createElement("video");
    outputPreview.src = `/api/requests/${id}/output.mp4`;
    outputPreview.parentElement.load();
  }
}

baseVideo.onchange = () => {
  const file = baseVideo.files[0];
  if(!file.type.startsWith("video/"))
    return alert("Это не видео...");
  basePreview.src = URL.createObjectURL(file);
  basePreview.parentElement.style.display = "";
  basePreview.parentElement.load();
};

overlayVideo.onchange = () => {
  const file = overlayVideo.files[0];
  if(!file.type.startsWith("video/"))
    return alert("Это не видео...");
  overlayPreview.src = URL.createObjectURL(file);
  overlayPreview.parentElement.style.display = "";
  overlayPreview.parentElement.load();
};

document.getElementById("start_processing").onclick = run;
