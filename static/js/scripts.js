document.addEventListener('DOMContentLoaded', function() {
    // Seat selection functionality
    initSeatSelection();
    
    // Show password toggle
    initPasswordToggle();
    
    // Initialize tooltips (if Bootstrap is used)
    initTooltips();
    
    // Initialize date inputs with min date
    initDateInputs();
    
    // Initialize dynamic forms for passenger details
    initPassengerForms();
});

function initSeatSelection() {
    const seatContainer = document.querySelector('.seat-map');
    if (!seatContainer) return;
    
    const seats = document.querySelectorAll('.seat.available');
    const selectedSeatsInput = document.getElementById('selected_seats');
    const selectedSeatsCounter = document.getElementById('selected-count');
    const selectedSeatsDisplay = document.getElementById('selected-seats-display');
    const totalPriceDisplay = document.getElementById('total-price');
    const pricePerSeat = document.getElementById('price-per-seat');
    const submitButton = document.getElementById('submit-seats');
    
    let selectedSeats = [];
    
    seats.forEach(seat => {
        seat.addEventListener('click', function() {
            const seatId = this.getAttribute('data-seat-id');
            const seatNumber = this.getAttribute('data-seat-number');
            
            if (this.classList.contains('selected')) {
                // Deselect seat
                this.classList.remove('selected');
                selectedSeats = selectedSeats.filter(id => id !== seatId);
                
                // Remove from selected seats display
                const displayItem = document.querySelector(`[data-display-seat="${seatNumber}"]`);
                if (displayItem) {
                    displayItem.remove();
                }
            } else {
                // Select seat
                this.classList.add('selected');
                selectedSeats.push(seatId);
                
                // Add to selected seats display
                if (selectedSeatsDisplay) {
                    const seatItem = document.createElement('span');
                    seatItem.classList.add('badge', 'bg-primary', 'me-1', 'mb-1');
                    seatItem.setAttribute('data-display-seat', seatNumber);
                    seatItem.textContent = seatNumber;
                    selectedSeatsDisplay.appendChild(seatItem);
                }
            }
            
            // Update hidden input with selected seats
            if (selectedSeatsInput) {
                selectedSeatsInput.value = selectedSeats.join(',');
            }
            
            // Update counter
            if (selectedSeatsCounter) {
                selectedSeatsCounter.textContent = selectedSeats.length;
            }
            
            // Update total price
            if (totalPriceDisplay && pricePerSeat) {
                const price = parseFloat(pricePerSeat.value);
                const totalPrice = selectedSeats.length * price;
                totalPriceDisplay.textContent = totalPrice.toFixed(2);
            }
            
            // Update submit button state
            if (submitButton) {
                submitButton.disabled = selectedSeats.length === 0;
            }
        });
    });
}

function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.password-toggle');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const passwordField = document.getElementById(this.getAttribute('data-target'));
            if (passwordField) {
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                
                // Toggle icon
                const icon = this.querySelector('i');
                if (icon) {
                    if (type === 'password') {
                        icon.classList.remove('fa-eye');
                        icon.classList.add('fa-eye-slash');
                    } else {
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                    }
                }
            }
        });
    });
}

function initTooltips() {
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
        tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
    }
}

function initDateInputs() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    if (dateInputs.length > 0) {
        const today = new Date().toISOString().split('T')[0];
        
        dateInputs.forEach(input => {
            // Set min date to today if not already set
            if (!input.getAttribute('min')) {
                input.setAttribute('min', today);
            }
        });
    }
}

function initPassengerForms() {
    const passengerForms = document.getElementById('passenger-forms');
    if (!passengerForms) return;
    
    const seatInputs = document.querySelectorAll('input[name="seat_id"]');
    
    if (seatInputs.length > 0) {
        // Add index to form fields to ensure unique names
        seatInputs.forEach((input, index) => {
            const form = input.closest('.passenger-form');
            if (form) {
                const formInputs = form.querySelectorAll('input, select');
                formInputs.forEach(formInput => {
                    const name = formInput.getAttribute('name');
                    if (name && name !== 'seat_id') {
                        formInput.setAttribute('name', `${name}-${index}`);
                    }
                });
            }
        });
    }
}

// Function to print ticket
function printTicket() {
    window.print();
}

// Function to validate search form
function validateSearchForm() {
    const originSelect = document.getElementById('origin');
    const destinationSelect = document.getElementById('destination');
    const dateInput = document.getElementById('date');
    const errorMessage = document.getElementById('search-error');
    
    if (!originSelect || !destinationSelect || !dateInput) return true;
    
    const origin = originSelect.value;
    const destination = destinationSelect.value;
    const date = dateInput.value;
    
    // Reset error message
    if (errorMessage) {
        errorMessage.textContent = '';
        errorMessage.classList.add('d-none');
    }
    
    // Check if all fields are filled
    if (!origin || !destination || !date) {
        if (errorMessage) {
            errorMessage.textContent = 'Please fill in all fields.';
            errorMessage.classList.remove('d-none');
        }
        return false;
    }
    
    // Check if origin and destination are different
    if (origin === destination) {
        if (errorMessage) {
            errorMessage.textContent = 'Origin and destination cannot be the same.';
            errorMessage.classList.remove('d-none');
        }
        return false;
    }
    
    // Check if date is not in the past
    const selectedDate = new Date(date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (selectedDate < today) {
        if (errorMessage) {
            errorMessage.textContent = 'Please select a date in the future.';
            errorMessage.classList.remove('d-none');
        }
        return false;
    }
    
    return true;
}

// Function to handle booking cancellation confirmation
function confirmCancellation(bookingId, bookingNumber) {
    if (confirm(`Are you sure you want to cancel booking #${bookingNumber}? This action cannot be undone.`)) {
        document.getElementById(`cancel-form-${bookingId}`).submit();
    }
}
