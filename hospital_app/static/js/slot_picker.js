/**
 * Interactive Appointment Date/Time Slot Picker (ES6+)
 * Communicates with Django API to show real-time available and booked slots
 */

document.addEventListener('DOMContentLoaded', function () {
    const doctorSelect = document.getElementById('id_doctor');
    const dateInput = document.getElementById('id_date');
    const slotSelect = document.getElementById('id_time_slot');
    const slotsContainer = document.getElementById('interactiveSlotsContainer');
    const slotNotice = document.getElementById('slotNotice');
    const feeDisplay = document.getElementById('summaryDoctorFee');
    const slotSummary = document.getElementById('summarySelectedSlot');
    const doctorSummary = document.getElementById('summaryDoctorName');
    const dateSummary = document.getElementById('summarySelectedDate');

    if (!doctorSelect || !dateInput) return;

    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
    if (!dateInput.value) {
        dateInput.value = today;
    }

    // Hide default select or keep it synchronized
    if (slotSelect) {
        slotSelect.style.display = 'none';
    }

    function updateSummary() {
        const selectedDoctorOption = doctorSelect.options[doctorSelect.selectedIndex];
        if (doctorSummary && selectedDoctorOption) {
            doctorSummary.textContent = selectedDoctorOption.text || 'Not selected';
        }
        if (dateSummary) {
            dateSummary.textContent = dateInput.value || 'Not selected';
        }
        if (slotSummary && slotSelect) {
            slotSummary.textContent = slotSelect.value || 'Please select a time slot';
        }
    }

    async function fetchSlots() {
        const doctorId = doctorSelect.value;
        const selectedDate = dateInput.value;

        updateSummary();

        if (!doctorId || !selectedDate) {
            if (slotNotice) {
                slotNotice.className = 'alert alert-info py-2 px-3 small';
                slotNotice.textContent = 'Please choose both a doctor and appointment date to view available time slots.';
                slotNotice.classList.remove('d-none');
            }
            if (slotsContainer) slotsContainer.innerHTML = '';
            return;
        }

        if (slotsContainer) {
            slotsContainer.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                    Checking real-time slot availability...
                </div>
            `;
        }

        try {
            const response = await fetch(`/api/doctor-slots/?doctor_id=${doctorId}&date=${selectedDate}`);
            if (!response.ok) {
                throw new Error('Failed to load slots');
            }
            const data = await response.json();

            // Update doctor fee display
            if (feeDisplay && data.fee !== undefined) {
                feeDisplay.textContent = `$${data.fee.toFixed(2)}`;
            }

            // Check if day is valid
            if (!data.is_available_day) {
                if (slotNotice) {
                    slotNotice.className = 'alert alert-warning py-2 px-3 small';
                    slotNotice.innerHTML = `
                        <strong>Notice:</strong> ${data.doctor_name} is normally not on schedule on <strong>${data.day_name}s</strong>.<br>
                        Available regular days: <span class="text-dark fw-bold">${data.available_days}</span>. Please choose another date.
                    `;
                    slotNotice.classList.remove('d-none');
                }
                if (slotsContainer) slotsContainer.innerHTML = '';
                if (slotSelect) slotSelect.value = '';
                return;
            }

            if (data.is_past) {
                if (slotNotice) {
                    slotNotice.className = 'alert alert-danger py-2 px-3 small';
                    slotNotice.textContent = 'Selected date is in the past. Please pick a current or upcoming date.';
                    slotNotice.classList.remove('d-none');
                }
                if (slotsContainer) slotsContainer.innerHTML = '';
                if (slotSelect) slotSelect.value = '';
                return;
            }

            // Normal state: render slots
            if (slotNotice) {
                const bookedCount = data.booked_slots.length;
                const totalCount = data.all_slots.length;
                const availCount = totalCount - bookedCount;
                slotNotice.className = 'alert alert-success py-2 px-3 small';
                slotNotice.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <span>Schedule on <strong>${data.day_name}</strong>: <strong>${availCount}</strong> available slots, <strong>${bookedCount}</strong> booked.</span>
                        <span class="badge bg-primary">Consultation Fee: $${data.fee.toFixed(2)}</span>
                    </div>
                `;
                slotNotice.classList.remove('d-none');
            }

            renderSlotsGrid(data.all_slots, data.booked_slots);

        } catch (error) {
            console.error('Error fetching slots:', error);
            if (slotNotice) {
                slotNotice.className = 'alert alert-danger py-2 px-3 small';
                slotNotice.textContent = 'Could not fetch time slots. Please try again or refresh the page.';
                slotNotice.classList.remove('d-none');
            }
        }
    }

    function renderSlotsGrid(allSlots, bookedSlots) {
        if (!slotsContainer) return;
        slotsContainer.innerHTML = '';

        const currentValue = slotSelect ? slotSelect.value : '';

        allSlots.forEach(slot => {
            const isBooked = bookedSlots.includes(slot);
            const isSelected = (!isBooked && currentValue === slot);

            const slotBtn = document.createElement('div');
            slotBtn.className = `slot-btn ${isBooked ? 'booked disabled' : ''} ${isSelected ? 'selected' : ''}`;
            slotBtn.setAttribute('data-slot', slot);

            let statusLabel = isBooked 
                ? '<span class="badge bg-danger text-white slot-status-indicator"><i class="bi bi-x-circle me-1"></i>Booked</span>'
                : '<span class="badge bg-success-subtle text-success slot-status-indicator"><i class="bi bi-check-circle me-1"></i>Available</span>';

            if (isSelected) {
                statusLabel = '<span class="badge bg-white text-primary slot-status-indicator"><i class="bi bi-hand-thumbs-up-fill me-1"></i>Selected</span>';
            }

            slotBtn.innerHTML = `
                <span class="slot-time"><i class="bi bi-clock me-1"></i>${slot}</span>
                ${statusLabel}
            `;

            if (!isBooked) {
                slotBtn.addEventListener('click', function () {
                    // Deselect previous
                    document.querySelectorAll('.slot-btn').forEach(btn => {
                        if (!btn.classList.contains('booked')) {
                            btn.classList.remove('selected');
                            const indicator = btn.querySelector('.slot-status-indicator');
                            if (indicator) {
                                indicator.className = 'badge bg-success-subtle text-success slot-status-indicator';
                                indicator.innerHTML = '<i class="bi bi-check-circle me-1"></i>Available';
                            }
                        }
                    });

                    // Select current
                    slotBtn.classList.add('selected');
                    const curIndicator = slotBtn.querySelector('.slot-status-indicator');
                    if (curIndicator) {
                        curIndicator.className = 'badge bg-white text-primary slot-status-indicator';
                        curIndicator.innerHTML = '<i class="bi bi-hand-thumbs-up-fill me-1"></i>Selected';
                    }

                    if (slotSelect) {
                        slotSelect.value = slot;
                    }

                    updateSummary();
                });
            }

            slotsContainer.appendChild(slotBtn);
        });

        // If the previously selected slot is now booked or reset, clear select
        if (bookedSlots.includes(currentValue) && slotSelect) {
            slotSelect.value = '';
            updateSummary();
        }
    }

    doctorSelect.addEventListener('change', fetchSlots);
    dateInput.addEventListener('change', fetchSlots);

    // Initial fetch if doctor and date are pre-selected
    if (doctorSelect.value && dateInput.value) {
        fetchSlots();
    }
});
