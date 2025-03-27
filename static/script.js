document.addEventListener('DOMContentLoaded', function() {
    // When a video card is clicked, load the video into the modal and display it
    document.querySelectorAll('.video-card').forEach(card => {
      card.addEventListener('click', function() {
        const videoSrc = card.getAttribute('data-video-src');
        const videoElement = document.getElementById('modalVideo');
        videoElement.querySelector('source').src = videoSrc;
        videoElement.load();
        $('#videoModal').modal('show');
      });
    });
  
    // Pause the video when the modal is closed
    $('#videoModal').on('hide.bs.modal', function() {
      const videoElement = document.getElementById('modalVideo');
      videoElement.pause();
    });
  });
  