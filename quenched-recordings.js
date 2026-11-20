(() => {
  'use strict';
  const PLAY_COUNT = 3;
  const choices = document.getElementById('recorded-choices');
  const buttons = Array.from(choices.querySelectorAll('button'));
  const recordings = buttons.map(button => {
    const panel = document.getElementById(button.getAttribute('aria-controls'));
    return {button, panel, video: panel.querySelector('video'), completed: 0};
  });

  for(const recording of recordings) {
    const {button, panel, video} = recording;
    panel.hidden = true;
    video.addEventListener('play', () => {
      if(recording.completed >= PLAY_COUNT) recording.completed = 0;
    });
    video.addEventListener('ended', () => {
      recording.completed += 1;
      if(recording.completed < PLAY_COUNT) {
        video.currentTime = 0;
        video.play().catch(() => {});
      }
    });
    button.addEventListener('click', () => {
      for(const other of recordings) {
        other.video.pause();
        other.panel.hidden = other !== recording;
        other.button.setAttribute('aria-expanded', String(other === recording));
      }
      recording.completed = 0;
      video.currentTime = 0;
      video.play().catch(() => {});
    });
  }
  choices.hidden = false;
})();
