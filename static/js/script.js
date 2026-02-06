const delButtons = document.querySelectorAll('.delete_btn');
        delButtons.forEach(delFunction => {
            delFunction.addEventListener('click', function(event) {
            const userConfirmation = window.confirm("Are you sure?");
	    if (userConfirmation) {
		console.log("Item Deleted!");
	    } 
	    else {
		event.preventDefault();
		console.log("Deletion Cancelled");
	    }
            });
});

const addForm = document.getElementById('addTermForm');
    
const addBtn = document.getElementById('addTermButton');
        addBtn.addEventListener('click', function(event) {
            if (addForm.style.display === "none" || addForm.style.display === ""){
		    addForm.style.display = "block";
            } else {
		    addForm.style.display = "none";
	    }});
