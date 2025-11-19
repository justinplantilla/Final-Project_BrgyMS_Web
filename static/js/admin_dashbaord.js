// Subtle card hover animation
document.querySelectorAll('.hover-animate').forEach(card => {
  card.addEventListener('mouseenter', () => {
    card.style.transform = 'translateY(-4px)';
    card.style.boxShadow = '0 10px 18px rgba(0,0,0,0.1)';
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = 'translateY(0)';
    card.style.boxShadow = '0 2px 6px rgba(0,0,0,0.08)';
  });
});

// Search functionality
document.getElementById('searchInput').addEventListener('input', function() {
  const query = this.value.toLowerCase();
  const cards = document.querySelectorAll('.card');

  cards.forEach(card => {
    const title = card.querySelector('h2').textContent.toLowerCase();
    const description = card.querySelector('p').textContent.toLowerCase();

    if (title.includes(query) || description.includes(query)) {
      card.style.display = 'block';
    } else {
      card.style.display = 'none';
    }
  });
});

// History modal functions
function openHistoryModal() {
  // Fetch activity history from API
  fetch('/api/activity-history')
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error('Error fetching activity history:', data.error);
        return;
      }

      // Populate Captain activities
      const captainContainer = document.getElementById('captainActivities');
      captainContainer.innerHTML = '';

      if (data.captain_activities.length === 0) {
        captainContainer.innerHTML = '<p class="text-gray-500 text-sm">No recent activities</p>';
      } else {
        data.captain_activities.forEach(activity => {
          const activityDiv = createActivityElement(activity, 'blue');
          captainContainer.appendChild(activityDiv);
        });
      }

      // Populate Secretary activities
      const secretaryContainer = document.getElementById('secretaryActivities');
      secretaryContainer.innerHTML = '';

      if (data.secretary_activities.length === 0) {
        secretaryContainer.innerHTML = '<p class="text-gray-500 text-sm">No recent activities</p>';
      } else {
        data.secretary_activities.forEach(activity => {
          const activityDiv = createActivityElement(activity, 'purple');
          secretaryContainer.appendChild(activityDiv);
        });
      }

      // Show modal
      document.getElementById('historyModal').classList.remove('hidden');
    })
    .catch(error => {
      console.error('Error fetching activity history:', error);
    });
}

function createActivityElement(activity, color) {
  const div = document.createElement('div');
  div.className = `bg-${color}-50 p-4 rounded-lg border-l-4 border-${color}-500`;

  const timeAgo = getTimeAgo(new Date(activity.timestamp));

  div.innerHTML = `
    <div class="flex justify-between items-start">
      <div>
        <p class="font-medium text-gray-800">${activity.action}</p>
        <p class="text-sm text-gray-600">${activity.details || 'No additional details'}</p>
      </div>
      <span class="text-xs text-gray-500">${timeAgo}</span>
    </div>
  `;

  return div;
}

function getTimeAgo(date) {
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;

  return date.toLocaleDateString();
}

function closeHistoryModal() {
  document.getElementById('historyModal').classList.add('hidden');
}

// Close modal when clicking outside
document.getElementById('historyModal').addEventListener('click', function(e) {
  if (e.target === this) {
    closeHistoryModal();
  }
});
