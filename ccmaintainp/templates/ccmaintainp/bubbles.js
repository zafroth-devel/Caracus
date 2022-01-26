            hold_data = data['message'];

            // Remove all items from the list and start again so no double ups
            $('#delete-question-type-id').find('option').remove().end();
            $('#delete_type_question_target_id').val('');

            // Add default
            $('#delete-question-type-id').append('<option value="">--Please choose an option--</option>');

            // Add a bunch of items
            $.each(hold_data, function (i, item) {

                $('#delete-question-type-id').append($('<option>', { 
                value: item.id,
                text : item.question_type 
                }));
            });
            // Set to default
            $('#delete-question-type-id').val('');

            // Act when the target changes (Project or Change)
            $('#delete_type_question_target_id').on('change', function(event) {


                // Immediately set question type to default stops erroneous selects on return
                $('#delete-question-type-id').val('');

                var item_list = $('#delete_type_question_target_id').val();

                // Act if target not the default
                if(item_list!==''){

                    // For all options
                    $.each(hold_data, function (i, item) {

                        // Enable all options and then selectively disable when not target
                        $('#delete-question-type-id option[value="'+item.id+'"]').removeAttr('disabled');

                        if(item.question_level!==item_list){

                            $('#delete-question-type-id option[value="'+item.id+'"]').attr('disabled', 'disabled');

                        }

                    });

                    // Enable previously disabled type select
                    $('#delete-question-type-id').removeAttr('disabled');

                } else {

                    // Disable type and set to default helps stop erroneous selects on return
                    $('#delete-question-type-id').attr('disabled','disabled');
                    $('#delete-question-type-id').val('');
                }

            });