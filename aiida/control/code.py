import enum
import os

from aiida.cmdline.dbenv_decorator import aiida_dbenv


class ErrorAccumulator(object):
    def __init__(self, *err_cls):
        self.err_cls = err_cls
        self.errors = {k: [] for k in self.err_cls}

    def accumulate_errors(self, original_function):
        def decorated_function(*args, **kwargs):
            self.run(original_function)

    @staticmethod
    def mark_accumulatable(accum_list):
        def accumulatable_decorator(method):
            if not hasattr(method, 'im_class'):
                raise AttributeError('@mark_accumulatable can only be used on methods')

            if not hasattr(method.im_class, accum_list):
                setattr(method.im_class, accum_list, [])

            getattr(method.im_class, accum_list).append(method.__name__)
            return method
        return accumulatable_decorator

    def run(self, function, *args, **kwargs):
        try:
            function(*args, **kwargs)
        except self.error_cls as err:
            self.errors[err.__class__].append(err)

    def run_all(self, accum_list, *args, **kwargs):
        for method in accum_list:
            self.run(method, *args, **kwargs)

    def success(self):
        return bool(not self.errors)

    def result(self, raise_error=Exception):
        if raise_error:
            self.raise_errors(raise_error)
        return self.success(), self.errors

    def raise_errors(self, raise_cls):
        if self.errors:
            raise raise_cls('{}'.format(self.errors))


class CodeBuilder(object):
    """Build a code with validation of attribute combinations"""

    def __init__(self, **kwargs):
        self._code_spec = kwargs
        self.validators = []
        self.err_acc = ErrorAccumulator(self.CodeValidationError)
        self.code_type = self._property('code_type')
        self.local_executable = self._property('local_executable')
        self.code_folder = self._property('code_folder')
        self.computer = self._property('computer')
        self.remote_abs_path = self._property('remote_abs_path')
        self.label = self._property('label')
        self.description = self._property('description')
        self.input_plugin = self._property('input_plugin')
        self.prepend_text = self._property('prepend_text')
        self.append_text = self._property('append_text')
        self.validate()

    def validate(self, raise_error=True):
        self.err_acc.run_all(self.validators)
        return err_acc.result(raise_error=self.CodeValidationError if raise_error else False)

    @aiida_dbenv
    def new(self):
        self.validate()

        from aiida.orm import Code

        if self.code_type == self.CodeType.STORE_AND_UPLOAD:
            file_list = [
                os.path.realpath(
                    os.path.join(self.code_folder, f)) for f in os.listdir(self.code_folder)
            ]
            code = Code(local_executable=self.code_rel_path, files=file_list)
        else:
            code = Code(remote_computer_exec=(self.computer, self.remote_abs_path))

        code.label = self.label
        code.description = self.description
        code.set_input_plugin_name(self.input_plugin)
        code.set_prepend_text(self.prepend_text)
        code.set_append_text(self.append_text)

        return code

    def _property(self, key):
        return property(self._getter(key), self._setter(key))

    def _getter(self, key):
        def getter(self):
            return self._code_spec.get(key)


    def _setter(self, key):
        def setter(self, value):
            self._set_code_attr(key, value)

    def _set_code_attr(self, key, value):
        backup = self._code_spec.copy()
        self._code_spec[key] = value
        success, _ = self.validate(raise_error=False)
        if not success:
            self._code_spec = backup
            self.validate()

    @ErrorAccumulator.mark_accumulatable('validators')
    def validate_upload_or_installed(self):
        if self.code_type not in self.CodeType:
            raise CodeValidationError('invalid code type: must be one of {}'.format(list(self.CodeType)))

    @ErrorAccumulator.mark_accumulatable('validators')
    def validate_upload(self):
        messages = []
        if self.code_type == self.CodeType.STORE_AND_UPLOAD:
            if self.computer:
                messages.append('invalid option for store-and-upload code: "computer"')
            if self.remote_abs_path:
                messages.append('invalid option for store-and-upload code: "remote_abs_path"')
        if messages:
            raise self.CodeValidationError('{}'.format(messages))

    @ErrorAccumulator.mark_accumulatable('validators')
    def validate_installed(self):
        messages = []
        if self.code_type == self.CodeType.ON_COMPUTER:
            if self.code_folder:
                messages.append('invalid options for on-computer code: "code_folder"')
            if self.code_rel_path:
                messages.append('invalid options for on-computer code: "code_rel_path"')
        if messages:
            raise CodeValidationError('{}'.format(messages))


    class CodeValidationError(Exception):
        def __init__(self, msg):
            super(CodeValidationError, self).__init__()
            self.msg = msg

        def __str__(self):
            return 'Code Validation Error: {}'.format(msg)

    class CodeType(enum.Enum):
        STORE_AND_UPLOAD = 'store in the db and upload'
        ON_COMPUTER = 'on computer'


