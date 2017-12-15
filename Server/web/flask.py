app = Flask(__name__)
CORS(app)


@app.route('/doc', methods=['GET'])
def getdoc():
    return json.dumps({"code": 0, "msg": "success", "redirect": "", "data": {
        'name': '/predict',
        'describe': 'Predict for the cobelt action'
    }})


@app.route('/predict', methods=['POST'])
def upload_file2():
    # print path
    print request.method
    # if request.method == 'POST':
    # check if the post request has the file part
    if 'file' not in request.files:
        # flash('No file part')
        return '{"code":1,"msg":"No file part","redirect":"","data":""}'
    file = request.files['file']

    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        # flash('No selected file')
        return '{"code":1,"msg":"No selected file","redirect":"","data":""}'

    # if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    # try:
    #     file.save(os.path.join(path, filename))
    # except:
    #     #print sys.exc_info()
    #     return json.dumps(Msg(1,str(sys.exc_info()[1]),"","").getDic())
    net.forward(data=_read_image2(file)[np.newaxis, ...])
    output_blob = net.blobs['prob']
    out_ori = output_blob.data.flatten()

    print out_ori