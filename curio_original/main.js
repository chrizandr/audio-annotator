'use strict';

/*
 * Purpose:
 *   Combines all the components of the interface. Creates each component, gets task
 *   data, updates components. When the user submits their work this class gets the workers
 *   annotations and other data and submits to the backend
 * Dependencies:
 *   AnnotationStages (src/annotation_stages.js), PlayBar & WorkflowBtns (src/components.js), 
 *   HiddenImg (src/hidden_image.js), colormap (colormap/colormap.min.js) , Wavesurfer (lib/wavesurfer.min.js)
 * Globals variable from other files:
 *   audio.html (task related):
 *       user_id, curio_id, task_id, total_num_tasks, num_required_tasks, experiment_id, condition_id, bonus_pay
 *   colormap.min.js:
 *       magma // color scheme array that maps 0 - 255 to rgb values
 *    
 */
function UrbanEars() {
    this.wavesurfer;
    this.playBar;
    this.stages;
    this.workflowBtns;
    this.tasks = [];
    this.currentTask;
    this.numRemainingTasks;
    this.taskStartTime;
    this.hiddenImage;
    // Boolean, true if currently sending http post request 
    this.sendingResponse = false;

    // Create color map for spectrogram
    var spectrogramColorMap = colormap({
        colormap: magma,
        nshades: 256,
        format: 'rgb',
        alpha: 1
    });

    // Create wavesurfer (audio visualization component)
    var height = 128;
    this.wavesurfer = Object.create(WaveSurfer);
    this.wavesurfer.init({
        container: '.audio_visual',
        waveColor: '#FF00FF',
        progressColor: '#FF00FF',
        // For the spectrogram the height is half the number of fftSamples
        fftSamples: height * 2,
        height: height,
        colorMap: spectrogramColorMap
    });

    // Create labels (labels that appear above each region)
    var labels = Object.create(WaveSurfer.Labels);
    labels.init({
        wavesurfer: this.wavesurfer,
        container: '.labels'
    });

    // Create hiddenImage, an image that is slowly revealed to a user as they annotate 
    // (only for this.currentTask.data.content.feedback === 'hiddenImage')
    this.hiddenImage = new HiddenImg('.hidden_img', 100);
    this.hiddenImage.create();

    // Create the play button and time that appear below the wavesurfer
    this.playBar = new PlayBar(this.wavesurfer);
    this.playBar.create();

    // Create the annotation stages that appear below the wavesurfer. The stages contain tags 
    // the users use to label a region in the audio clip
    this.stages = new AnnotationStages(this.wavesurfer, this.hiddenImage);
    this.stages.create();

    // Create Workflow btns (submit and exit)
    this.workflowBtns = new WorkflowBtns('/experiments/' + experiment_id + '/workflow/next');
    this.workflowBtns.create();

    this.addEvents();
}

UrbanEars.prototype = {

    addWaveSurferEvents: function() {
        var my = this;

        // function that moves the vertical progress bar to the current time in the audio clip
        var updateProgressBar = function () {
            var progress = my.wavesurfer.getCurrentTime() / my.wavesurfer.getDuration();
            my.wavesurfer.seekTo(progress);
        };

        // Update vertical progress bar to the currentTime when the sound clip is 
        // finished or paused since it is only updated on audioprocess
        this.wavesurfer.on('pause', updateProgressBar);
        this.wavesurfer.on('finish', updateProgressBar);    

        // When a new sound file is loaded into the wavesurfer update the  play bar, update the 
        // annotation stages back to stage 1, update when the user started the task, update the workflow buttons.
        // Also if the user is suppose to get hidden image feedback, append that component to the page
        this.wavesurfer.on('ready', function () {
            my.playBar.update();
            my.stages.updateStage(1);
            my.updateTaskTime();
            my.workflowBtns.update();
            if (my.currentTask.data.content.feedback === 'hiddenImage') {
                my.hiddenImage.append(static_url + my.currentTask.data.content.imgUrl);
            }
        });
    },

    updateTaskTime: function() {
        this.taskStartTime = new Date().getTime();
    },

    // Update the #task-progress-bar element to contain how many task the user has completed out of the total.
    // The element will also contain a message about how much bonus pay they will get for the clip if they have 
    // completed more then the required amount
    updateProgress: function() {
        var currentTaskNumber = (total_num_tasks - this.numRemainingTasks) + 1;
        var bonusText = 'Bonus for this clip: ' + bonus_pay * 100 + ' cents | ';
        var text = (currentTaskNumber > num_required_tasks) ? bonusText + 'Progress: ' : 'Progress: ';
        var progress = $('<b>', {
            text: text
        });
        var value = $('<span>', {
            text: currentTaskNumber + ' / ' + total_num_tasks
        });
        $('#task-progress-bar').html([progress, value]);
        // Update clip & time tracker of Header
        $('#recording-index').html(recordingIndex);
        $('#time-remaining').html((numRecordings - recordingIndex) * 1.5 + 5); // e.g. each clip should take 1.5 minutes, and all post-annotation tasks 5 mins.
    },

    // If the user has completed more than the required amount of tasks, show the exit button
    updateExitBtnFlag: function() {
        var numCompletedTasks = total_num_tasks - this.numRemainingTasks;
        var shouldShowExit = experiment_id && (numCompletedTasks >= num_required_tasks)
        this.workflowBtns.setExitBtnFlag(shouldShowExit);
    },

    // Event Handler, if the user clicks submit annotations call submitAnnotations
    addWorkflowBtnEvents: function() {
        $(this.workflowBtns).on('submit-annotations', this.submitAnnotations.bind(this));
    },

    addEvents: function() {
        this.addWaveSurferEvents();
        this.addWorkflowBtnEvents();
    },

    // Update the task specific data of the interfaces components
    update: function() {
        this.currentTask = this.tasks.shift();

        // In the case where the api returns the content field as a string, convert it to JSON
        if (typeof this.currentTask.data.content === 'string') {
            this.currentTask.data.content = JSON.parse(this.currentTask.data.content);
        }

        var my = this;

        var mainUpdate = function(annotationSolutions) {
            // Update the task progress text to show the user how many taks they have completed
            my.updateProgress();
            // Update weither the exit button should be shown
            my.updateExitBtnFlag();

            // Update the different tags the user can use to annotate, also update the solutions to the
            // annotation task if the user is suppose to recieve feedback
            var proximityTags = my.currentTask.data.content.proximityTag;
            var annotationTags = my.currentTask.data.content.annotationTag;
            var tutorialVideoURL = my.currentTask.data.content.tutorialVideoURL;
            var alwaysShowTags = my.currentTask.data.content.alwaysShowTags;
            my.stages.reset(
                proximityTags,
                annotationTags,
                annotationSolutions,
                alwaysShowTags
            );

            // set video url
            $('#tutorial-video').attr('src', tutorialVideoURL);

            // Update the visualization type and the feedback type and load in the new audio clip
            my.wavesurfer.params.visualization = my.currentTask.data.content.visualization; // invisible, spectrogram, waveform
            my.wavesurfer.params.feedback = my.currentTask.data.content.feedback; // hiddenImage, silent, notify, none 
            my.wavesurfer.load(my.currentTask.data.url);
        };

        if (this.currentTask.data.content.feedback !== 'none') {
            // If the current task gives the user feedback, load the tasks solutions and then update
            // interface components
            $.getJSON(static_url + this.currentTask.data.content.annotationSolutionsUrl)
            .done(function(data) {
                mainUpdate(data);
            })
            .fail(function() {
                alert('Error: Unable to retrieve annotation solution set');
            });
        } else {
            // If not, there is no need to make an additional request. Just update task specific data right away
            mainUpdate({});
        }
    },

    // Update the interface with the next task's data
    loadNextTask: function() {
        var my = this;
        if (this.tasks.length === 0) {
            // If there is no more tasks in the list load 3 more
            var data = {
                task: task_id,
                page_size: 3
            }
            if (experiment_id) {
                data.experiment = experiment_id;
                data.condition = condition_id;
            } else {
                data.public = 'True';
            }
            $.getJSON('/api/route/', data)
            .done(function(data) {
                if (data.results.length > 0) {
                    my.numRemainingTasks = data.count;
                    my.tasks = data.results;
                    my.update();
                } else {
                    // If there is no more tasks for the user to complete
                    if (experiment_id) {
                        window.location = '/experiments/' + experiment_id + '/workflow/next';
                    } else {
                        $('#ending_modal p').html(
                            'Wow! You\'ve labeled <strong>all</strong> the sound clips for this project.' +
                            'Thanks so much for helping us out!'
                        );
                        $('#ending_modal').openModal({dismissible: false});
                    }
                }
            })
            .fail(function() {
                alert('Error: Unable to retrieve more tasks');
            });
        } else {
            // Update the interface to the next task in the list (this.tasks)
            this.update();
        }
    },

    // Collect data about users annotations and submit it to the backend
    submitAnnotations: function() {
        // Check if all the regions have been labeled before submitting
        if (this.stages.annotationDataValidationCheck()) {
            if (this.sendingResponse) {
                // If it is already sending a post with the data, do nothing
                return;
            }
            this.sendingResponse = true;
            // Get data about the annotations the user has created
            var content = {
                task_start_time: this.taskStartTime,
                task_end_time: new Date().getTime(),
                visualization: this.wavesurfer.params.visualization,
                annotations: this.stages.getAnnotations(),
                deleted_annotations: this.stages.getDeletedAnnotations(),
                // List of the different types of actions they took to create the annotations
                annotation_events: this.stages.getEvents(),
                // List of actions the user took to play and pause the audio
                play_events: this.playBar.getEvents(),
                // Boolean, if at the end, the user was shown what city the clip was recorded in
                final_solution_shown: this.stages.aboveThreshold()
            };

            if (this.stages.aboveThreshold()) {
                // If the user is suppose to recieve feedback and got enough of the annotations correct
                // display the city the clip was recorded for 2 seconds and then submit their work
                var my = this;
                this.stages.displaySolution();
                setTimeout(function() {
                    my.post(content);
                }, 2000);
            } else {
                this.post(content);
            }
        }
    },

    // Make POST request, passing back the content data. On success load in the next task
    post: function (content) {
        $('#loading_modal').openModal({dismissible: false});
        var my = this;
        var data = {
            content: content,
            owner: user_id,
            data: this.currentTask.data.id,
            task: task_id,
            curio: curio_id,
            csrfmiddlewaretoken: csrftoken
        };
        if (experiment_id) {
            data.experiment = experiment_id;
            data.condition = condition_id;
        }
        $.ajax({
            type: 'POST',
            url: '/api/response/',
            contentType: 'application/json',
            data: JSON.stringify(data)
        })
        .done(function(data) {
            my.numRemainingTasks -= 1;
            // If the last task had a hiddenImage component, remove it
            if (my.currentTask.data.content.feedback === 'hiddenImage') {
                my.hiddenImage.remove();
            }
            my.loadNextTask();
        })
        .fail(function() {
            alert('Error: Unable to Submit Annotations');
        })
        .always(function() {
            // No longer sending response
            my.sendingResponse = false;
            setTimeout(function(){$('#loading_modal').closeModal();}, 2000);
        });
    }

};


function main() {
    // Create all the components
    var urbanEars = new UrbanEars();
    // Load the first audio annotation task
    urbanEars.loadNextTask();
}
main();