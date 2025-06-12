document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    // Get all DOM elements
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const resultArea = document.getElementById('resultArea');
    const previewImage = document.getElementById('previewImage');
    const predictionText = document.getElementById('predictionText');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const uploadAgainBtn = document.getElementById('uploadAgainBtn');
    console.log('Elements found:', {fileInput, uploadArea, resultArea, previewImage, predictionText, loadingIndicator});

    // File input change handler
    fileInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            
            // Display image preview
            const reader = new FileReader();
            reader.onload = function(event) {
                previewImage.src = event.target.result;
                previewImage.style.display = 'block';
            };
            reader.readAsDataURL(file);
            
            // Show loading state
            uploadArea.style.display = 'none';
            loadingIndicator.classList.remove('hidden');
            resultArea.classList.add('hidden');
            
            // Prepare form data for upload
            const formData = new FormData();
            formData.append('file', file);
            
            console.log('Sending request to server...');
            // Send to backend for processing
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Server response:', data);
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Display results
                console.log('Displaying results...');
                displayResults(data);
            })
            .catch(error => {
                console.error('Error:', error);
                displayError(error.message);
            });
        }
    });
    
    // Function to display successful results
    function displayResults(data) {
        console.log('Starting displayResults with data:', data);
        // Format the prediction text (replace underscores with spaces and capitalize)
        const formattedPrediction = data.prediction
            .replace(/_/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
            
        // Update the prediction text
        console.log('Setting prediction text to:', formattedPrediction);
        predictionText.textContent = formattedPrediction;
        predictionText.style.color = '#2c3e50';
        
        // Show the result area and hide loading
        console.log('Hiding loading indicator');
        loadingIndicator.classList.add('hidden');
        console.log('Showing result area');
        resultArea.classList.remove('hidden');
        
        console.log('Result area classes:', resultArea.className);
        console.log('Loading indicator classes:', loadingIndicator.className);
        
        // Update the image source
        if (data.image_url) {
            console.log('Setting image source to:', data.image_url);
            // Create a new image to handle loading
            const img = new Image();
            img.onload = function() {
                console.log('Image loaded successfully');
                previewImage.src = this.src;
                previewImage.style.display = 'block';
                console.log('Image display style:', previewImage.style.display);
            };
            img.onerror = function(err) {
                console.error('Error loading image:', data.image_url, err);
            };
            img.src = data.image_url + '?' + new Date().getTime(); // Add timestamp to prevent caching
            console.log('Image source set, waiting for load...');
        }
    }
    
    // Function to display errors
    function displayError(message) {
        predictionText.textContent = `Error: ${message}`;
        predictionText.style.color = '#e74c3c';
        loadingIndicator.classList.add('hidden');
        resultArea.classList.remove('hidden');
    }
    
    // Reset functionality when clicking results
    resultArea.addEventListener('click', function() {
        resetUploader();
    });
    // uploadAgainBtn.addEventListener('click', function(e) {
    //     e.stopPropagation(); // Prevent event bubbling
    //     resetUploader();
    // });
    // Function to reset the upload interface
    function resetUploader() {
        fileInput.value = '';
        previewImage.style.display = 'none';
        predictionText.textContent = '';
        predictionText.style.color = '';
        resultArea.classList.add('hidden');
        uploadArea.style.display = 'block';
    }
});