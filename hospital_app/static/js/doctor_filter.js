/**
 * Doctor List Filtering & Search (ES6+)
 * Provides instant department filtering and real-time text search
 */

document.addEventListener('DOMContentLoaded', function () {
    const filterPills = document.querySelectorAll('.dept-pill');
    const doctorCards = document.querySelectorAll('.doctor-item');
    const searchInput = document.getElementById('doctorSearchInput');
    const noResultsDiv = document.getElementById('noDoctorsFound');
    const countDisplay = document.getElementById('visibleDoctorCount');

    let currentDept = 'all';
    let searchQuery = '';

    function filterDoctors() {
        let visibleCount = 0;

        doctorCards.forEach(card => {
            const cardDept = card.getAttribute('data-department') || '';
            const cardName = (card.getAttribute('data-name') || '').toLowerCase();
            const cardSpec = (card.getAttribute('data-specialization') || '').toLowerCase();
            const cardQual = (card.getAttribute('data-qualification') || '').toLowerCase();

            const matchesDept = (currentDept === 'all' || cardDept.toLowerCase() === currentDept.toLowerCase());
            const matchesSearch = !searchQuery ||
                cardName.includes(searchQuery) ||
                cardSpec.includes(searchQuery) ||
                cardQual.includes(searchQuery);

            if (matchesDept && matchesSearch) {
                card.style.display = 'block';
                card.classList.add('animate__fadeIn');
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        if (countDisplay) {
            countDisplay.textContent = visibleCount;
        }

        if (noResultsDiv) {
            if (visibleCount === 0) {
                noResultsDiv.classList.remove('d-none');
            } else {
                noResultsDiv.classList.add('d-none');
            }
        }
    }

    // Event listeners for Department Filter Pills
    filterPills.forEach(pill => {
        pill.addEventListener('click', function () {
            filterPills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');

            currentDept = this.getAttribute('data-dept') || 'all';
            filterDoctors();
        });
    });

    // Event listener for search input
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            searchQuery = e.target.value.trim().toLowerCase();
            filterDoctors();
        });
    }

    // Doctor Details Modal Population
    const doctorModal = document.getElementById('doctorDetailModal');
    if (doctorModal) {
        doctorModal.addEventListener('show.bs.modal', function (event) {
            const triggerBtn = event.relatedTarget;
            if (!triggerBtn) return;

            const name = triggerBtn.getAttribute('data-name') || '';
            const dept = triggerBtn.getAttribute('data-dept') || '';
            const spec = triggerBtn.getAttribute('data-spec') || '';
            const fee = triggerBtn.getAttribute('data-fee') || '';
            const days = triggerBtn.getAttribute('data-days') || '';
            const exp = triggerBtn.getAttribute('data-exp') || '';
            const qual = triggerBtn.getAttribute('data-qual') || '';
            const bio = triggerBtn.getAttribute('data-bio') || '';
            const email = triggerBtn.getAttribute('data-email') || '';
            const phone = triggerBtn.getAttribute('data-phone') || '';
            const doctorId = triggerBtn.getAttribute('data-id') || '';
            const img = triggerBtn.getAttribute('data-img') || '';

            document.getElementById('modalDocName').textContent = name;
            document.getElementById('modalDocDept').textContent = dept;
            document.getElementById('modalDocSpec').textContent = spec;
            document.getElementById('modalDocFee').textContent = '$' + fee;
            document.getElementById('modalDocDays').textContent = days;
            document.getElementById('modalDocExp').textContent = exp + ' Years Experience';
            document.getElementById('modalDocQual').textContent = qual;
            document.getElementById('modalDocBio').textContent = bio || 'No biography available.';
            document.getElementById('modalDocEmail').textContent = email || 'contact@hospital.com';
            document.getElementById('modalDocPhone').textContent = phone || '+1 (555) 019-2834';

            const modalImg = document.getElementById('modalDocImg');
            if (modalImg) {
                if (img) {
                    modalImg.src = img;
                    modalImg.classList.remove('d-none');
                } else {
                    modalImg.classList.add('d-none');
                }
            }

            const bookBtn = document.getElementById('modalBookBtn');
            if (bookBtn) {
                bookBtn.href = `/book/?doctor=${doctorId}`;
            }
        });
    }

    // Initial run
    filterDoctors();
});
