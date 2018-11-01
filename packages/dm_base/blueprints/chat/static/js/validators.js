function validate(value, validators) {
    let errors = []
    for (let key in validators){
        if (window["validate_"+key]){
            error = window["validate_"+key](value, validators['key']);
            if (error){
                errors.push(error);
            }
        }
    }
    console.log(errors)
    return errors
}

function validate_required(value){
    if (!value) {
        return "This field is required";
    }
    return null;
}

function validate_jwt(value){
//    TODO Implement the jwt validation
    return null;
}
