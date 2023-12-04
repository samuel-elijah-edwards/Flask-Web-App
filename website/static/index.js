function deleteNote(noteId) {
    fetch("/delete-note", {
        method: 'POST',
        body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
        window.location.href = "/"
    });
}


function deleteFile(fileId) {
    fetch("/delete-file", {
        method: 'POST',
        body: JSON.stringify({ fileId: fileId }),
    }).then((_res) => {
        window.location.reload(); // Reload the page after successful deletion
    });
}