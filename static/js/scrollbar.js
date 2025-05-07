// static/js/scrollbar.js
// Create a custom scrollbar for the chat input textarea

document.addEventListener('DOMContentLoaded', function() {
  const container = document.querySelector('.chat-input-container');
  if (!container) return;
  const textarea = container.querySelector('textarea');
  if (!textarea) return;

  // Create track and thumb elements
  const track = document.createElement('div');
  track.className = 'custom-scrollbar-track';
  const thumb = document.createElement('div');
  thumb.className = 'custom-scrollbar-thumb';
  container.appendChild(track);
  container.appendChild(thumb);

  // Update thumb size and position
  function updateThumb() {
    // Only show when textarea is in scroll mode (overflowY auto)
    const comp = window.getComputedStyle(textarea).overflowY;
    if (comp !== 'auto') {
      track.style.display = 'none';
      thumb.style.display = 'none';
      return;
    }
    // Only show when there is overflow content
    if (textarea.scrollHeight <= textarea.clientHeight) {
      track.style.display = 'none';
      thumb.style.display = 'none';
      return;
    }
    // Show scrollbar when overflowing and in scroll mode
    track.style.display = 'block';
    thumb.style.display = 'block';
    const height = textarea.clientHeight;
    const scrollHeight = textarea.scrollHeight;
    const trackHeight = track.clientHeight;

    // Calculate thumb height (min 20px)
    const thumbHeight = Math.max((height / scrollHeight) * trackHeight, 20);
    thumb.style.height = thumbHeight + 'px';

    // Calculate thumb top position
    const scrollRatio = textarea.scrollTop / (scrollHeight - height);
    const topOffset = track.offsetTop + scrollRatio * (trackHeight - thumbHeight);
    thumb.style.top = topOffset + 'px';
  }

  // Hide scrollbar initially
  track.style.display = 'none';
  thumb.style.display = 'none';

  // Initialize padding to avoid text hidden under thumb
  const originalPaddingRight = window.getComputedStyle(textarea).paddingRight;
  const pad = 45; // space for + button and small text gap
  textarea.style.setProperty('padding-right', `calc(${originalPaddingRight} + ${pad}px)`, 'important');

  // Event listeners
  textarea.addEventListener('scroll', updateThumb);
  textarea.addEventListener('input', updateThumb);
  window.addEventListener('resize', updateThumb);

  // Initial update
  updateThumb();

  // Make scrollbar interactive: drag thumb and click track
  let isDrag = false, startY = 0, startScrollTop = 0;
  thumb.addEventListener('mousedown', function(e) {
    e.preventDefault();
    isDrag = true;
    startY = e.clientY;
    startScrollTop = textarea.scrollTop;
    document.body.classList.add('custom-scrollbar-dragging');
  });
  document.addEventListener('mousemove', function(e) {
    if (!isDrag) return;
    const dy = e.clientY - startY;
    const trackHeight = track.clientHeight;
    const thumbHeight = thumb.clientHeight;
    const scrollableHeight = textarea.scrollHeight - textarea.clientHeight;
    const maxThumbOffset = trackHeight - thumbHeight;
    const scrollRatio = dy / maxThumbOffset;
    textarea.scrollTop = startScrollTop + scrollRatio * scrollableHeight;
    updateThumb();
  });
  document.addEventListener('mouseup', function() {
    if (isDrag) {
      isDrag = false;
      document.body.classList.remove('custom-scrollbar-dragging');
    }
  });
  track.addEventListener('click', function(e) {
    e.preventDefault();
    const rect = track.getBoundingClientRect();
    const clickY = e.clientY - rect.top;
    const trackHeight = track.clientHeight;
    const thumbHeight = thumb.clientHeight;
    const scrollableHeight = textarea.scrollHeight - textarea.clientHeight;
    const scrollRatio = clickY / (trackHeight - thumbHeight);
    textarea.scrollTop = scrollRatio * scrollableHeight;
    updateThumb();
  });
}); 