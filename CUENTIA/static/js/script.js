document.addEventListener('DOMContentLoaded', function() {
  // Dropdown menus
  const dropdownToggles = document.querySelectorAll('[data-toggle="dropdown"]');

  dropdownToggles.forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();

      const targetId = this.getAttribute('data-target');
      const target = document.getElementById(targetId);

      if (target) {
        target.classList.toggle('show');
      }
    });
  });

  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    const dropdowns = document.querySelectorAll('.dropdown-menu.show');
    dropdowns.forEach(dropdown => {
      if (!dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
      }
    });
  });

  // Tabs
  const tabToggles = document.querySelectorAll('[data-toggle="tab"]');

  tabToggles.forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      e.preventDefault();

      // Remove active class from all tabs
      const tabContainer = this.closest('.tabs');
      const tabs = tabContainer.querySelectorAll('[data-toggle="tab"]');
      tabs.forEach(tab => tab.classList.remove('active'));

      // Add active class to clicked tab
      this.classList.add('active');

      // Show target content and hide others
      const targetId = this.getAttribute('data-target');
      const tabContents = document.querySelectorAll('.tab-content');

      tabContents.forEach(content => {
        content.style.display = 'none';
      });

      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.style.display = 'block';
      }
    });
  });

  // Mobile sidebar toggle
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function() {
      sidebar.classList.toggle('show');
    });
  }

  // Favorite toggle
  const favoriteButtons = document.querySelectorAll('.favorite-toggle');

  favoriteButtons.forEach(button => {
    button.addEventListener('click', function() {
      this.classList.toggle('active');

      // Update icon
      const icon = this.querySelector('i');
      if (icon) {
        if (this.classList.contains('active')) {
          icon.classList.remove('far');
          icon.classList.add('fas');
        } else {
          icon.classList.remove('fas');
          icon.classList.add('far');
        }
      }
    });
  });
});