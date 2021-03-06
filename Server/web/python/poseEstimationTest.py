import cv2 as cv
import numpy as np
import scipy
import PIL.Image
import math
import caffe
import time
from config_reader import config_reader
import util
import copy
import matplotlib
# matplotlib inline
import pylab as plt
from scipy.ndimage.filters import gaussian_filter


class PoseEstimation():
    def __init__(self):
        # init model
        self.param, self.model = config_reader()
        # multiplier = [x * model['boxsize'] / oriImg.shape[0] for x in param['scale_search']]
        if self.param['use_gpu']:
            print "gpu model"
            caffe.set_mode_gpu()
            caffe.set_device(self.param['GPUdeviceNumber'])  # set to your device!
        else:
            print "cpu model"
            caffe.set_mode_cpu()

        self.net = caffe.Net(self.model['deployFile'], self.model['caffemodel'], caffe.TEST)
        self.resultImagePath = ""

    # return center keypoints
    def KeypointDetection(self, oriImg_path, render_image_path):

        caffe.set_mode_gpu()
        caffe.set_device(self.param['GPUdeviceNumber'])

        oriImg = cv.imread(oriImg_path)
        print "image size:", oriImg.shape
        multiplier = [x * self.model['boxsize'] / oriImg.shape[0] for x in self.param['scale_search']]
        # get heatmap and paf map
        heatmap_avg = np.zeros((oriImg.shape[0], oriImg.shape[1], 19))
        paf_avg = np.zeros((oriImg.shape[0], oriImg.shape[1], 38))
        for m in range(len(multiplier)):
            scale = multiplier[m]
            imageToTest = cv.resize(oriImg, (0, 0), fx=scale, fy=scale, interpolation=cv.INTER_CUBIC)
            imageToTest_padded, pad = util.padRightDownCorner(imageToTest, self.model['stride'], self.model['padValue'])
            print imageToTest_padded.shape
            self.net.blobs['data'].reshape(*(1, 3, imageToTest_padded.shape[0], imageToTest_padded.shape[1]))

            # self.net.forward() # dry run
            self.net.blobs['data'].data[...] = np.transpose(np.float32(imageToTest_padded[:, :, :, np.newaxis]),
                                                            (3, 2, 0, 1)) / 256 - 0.5;
            start_time = time.time()
            output_blobs = self.net.forward()
            print('At scale %d, The CNN took %.2f ms.' % (m, 1000 * (time.time() - start_time)))

            # extract outputs, resize, and remove padding
            heatmap = np.transpose(np.squeeze(self.net.blobs[output_blobs.keys()[1]].data),
                                   (1, 2, 0))  # output 1 is heatmaps
            heatmap = cv.resize(heatmap, (0, 0), fx=self.model['stride'], fy=self.model['stride'],
                                interpolation=cv.INTER_CUBIC)
            heatmap = heatmap[:imageToTest_padded.shape[0] - pad[2], :imageToTest_padded.shape[1] - pad[3], :]
            heatmap = cv.resize(heatmap, (oriImg.shape[1], oriImg.shape[0]), interpolation=cv.INTER_CUBIC)

            paf = np.transpose(np.squeeze(self.net.blobs[output_blobs.keys()[0]].data), (1, 2, 0))  # output 0 is PAFs
            paf = cv.resize(paf, (0, 0), fx=self.model['stride'], fy=self.model['stride'], interpolation=cv.INTER_CUBIC)
            paf = paf[:imageToTest_padded.shape[0] - pad[2], :imageToTest_padded.shape[1] - pad[3], :]
            paf = cv.resize(paf, (oriImg.shape[1], oriImg.shape[0]), interpolation=cv.INTER_CUBIC)

            heatmap_avg = heatmap_avg + heatmap / len(multiplier)
            paf_avg = paf_avg + paf / len(multiplier)
        # --------------------------------------------
        # get all peaks
        print heatmap_avg.shape
        # plt.imshow(heatmap_avg[:,:,2])

        all_peaks = []
        peak_counter = 0

        for part in range(19 - 1):
            x_list = []
            y_list = []
            map_ori = heatmap_avg[:, :, part]
            map = gaussian_filter(map_ori, sigma=3)

            map_left = np.zeros(map.shape)
            map_left[1:, :] = map[:-1, :]
            map_right = np.zeros(map.shape)
            map_right[:-1, :] = map[1:, :]
            map_up = np.zeros(map.shape)
            map_up[:, 1:] = map[:, :-1]
            map_down = np.zeros(map.shape)
            map_down[:, :-1] = map[:, 1:]

            peaks_binary = np.logical_and.reduce(
                (map >= map_left, map >= map_right, map >= map_up, map >= map_down, map > self.param['thre1']))
            peaks = zip(np.nonzero(peaks_binary)[1], np.nonzero(peaks_binary)[0])  # note reverse
            peaks_with_score = [x + (map_ori[x[1], x[0]],) for x in peaks]
            id = range(peak_counter, peak_counter + len(peaks))
            peaks_with_score_and_id = [peaks_with_score[i] + (id[i],) for i in range(len(id))]

            all_peaks.append(peaks_with_score_and_id)
            peak_counter += len(peaks)

        # --------------------------------------------
        # find connection in the specified sequence, center 29 is in the position 15
        limbSeq = [[2, 3], [2, 6], [3, 4], [4, 5], [6, 7], [7, 8], [2, 9], [9, 10], \
                   [10, 11], [2, 12], [12, 13], [13, 14], [2, 1], [1, 15], [15, 17], \
                   [1, 16], [16, 18], [3, 17], [6, 18]]
        # the middle joints heatmap correpondence
        mapIdx = [[31, 32], [39, 40], [33, 34], [35, 36], [41, 42], [43, 44], [19, 20], [21, 22], \
                  [23, 24], [25, 26], [27, 28], [29, 30], [47, 48], [49, 50], [53, 54], [51, 52], \
                  [55, 56], [37, 38], [45, 46]]

        connection_all = []
        special_k = []
        mid_num = 10

        for k in range(len(mapIdx)):
            score_mid = paf_avg[:, :, [x - 19 for x in mapIdx[k]]]
            candA = all_peaks[limbSeq[k][0] - 1]
            candB = all_peaks[limbSeq[k][1] - 1]
            nA = len(candA)
            nB = len(candB)
            indexA, indexB = limbSeq[k]
            if (nA != 0 and nB != 0):
                connection_candidate = []
                for i in range(nA):
                    for j in range(nB):
                        vec = np.subtract(candB[j][:2], candA[i][:2])
                        norm = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
                        vec = np.divide(vec, norm)

                        startend = zip(np.linspace(candA[i][0], candB[j][0], num=mid_num), \
                                       np.linspace(candA[i][1], candB[j][1], num=mid_num))

                        vec_x = np.array([score_mid[int(round(startend[I][1])), int(round(startend[I][0])), 0] \
                                          for I in range(len(startend))])
                        vec_y = np.array([score_mid[int(round(startend[I][1])), int(round(startend[I][0])), 1] \
                                          for I in range(len(startend))])

                        score_midpts = np.multiply(vec_x, vec[0]) + np.multiply(vec_y, vec[1])
                        score_with_dist_prior = sum(score_midpts) / len(score_midpts) + min(
                            0.5 * oriImg.shape[0] / norm - 1, 0)
                        criterion1 = len(np.nonzero(score_midpts > self.param['thre2'])[0]) > 0.8 * len(score_midpts)
                        criterion2 = score_with_dist_prior > 0
                        if criterion1 and criterion2:
                            connection_candidate.append(
                                [i, j, score_with_dist_prior, score_with_dist_prior + candA[i][2] + candB[j][2]])

                connection_candidate = sorted(connection_candidate, key=lambda x: x[2], reverse=True)
                connection = np.zeros((0, 5))
                for c in range(len(connection_candidate)):
                    i, j, s = connection_candidate[c][0:3]
                    if (i not in connection[:, 3] and j not in connection[:, 4]):
                        connection = np.vstack([connection, [candA[i][3], candB[j][3], s, i, j]])
                        if (len(connection) >= min(nA, nB)):
                            break

                connection_all.append(connection)
            else:
                special_k.append(k)
                connection_all.append([])

        # -----------------------------------------------
        # get all person keypoint detection
        # last number in each row is the total parts number of that person
        # the second last number in each row is the score of the overall configuration
        subset = -1 * np.ones((0, 20))
        candidate = np.array([item for sublist in all_peaks for item in sublist])

        for k in range(len(mapIdx)):
            if k not in special_k:
                partAs = connection_all[k][:, 0]
                partBs = connection_all[k][:, 1]
                indexA, indexB = np.array(limbSeq[k]) - 1

                for i in range(len(connection_all[k])):  # = 1:size(temp,1)
                    found = 0
                    subset_idx = [-1, -1]
                    for j in range(len(subset)):  # 1:size(subset,1):
                        if subset[j][indexA] == partAs[i] or subset[j][indexB] == partBs[i]:
                            subset_idx[found] = j
                            found += 1

                    if found == 1:
                        j = subset_idx[0]
                        if (subset[j][indexB] != partBs[i]):
                            subset[j][indexB] = partBs[i]
                            subset[j][-1] += 1
                            subset[j][-2] += candidate[partBs[i].astype(int), 2] + connection_all[k][i][2]
                    elif found == 2:  # if found 2 and disjoint, merge them
                        j1, j2 = subset_idx
                        print "found = 2"
                        membership = ((subset[j1] >= 0).astype(int) + (subset[j2] >= 0).astype(int))[:-2]
                        if len(np.nonzero(membership == 2)[0]) == 0:  # merge
                            subset[j1][:-2] += (subset[j2][:-2] + 1)
                            subset[j1][-2:] += subset[j2][-2:]
                            subset[j1][-2] += connection_all[k][i][2]
                            subset = np.delete(subset, j2, 0)
                        else:  # as like found == 1
                            subset[j1][indexB] = partBs[i]
                            subset[j1][-1] += 1
                            subset[j1][-2] += candidate[partBs[i].astype(int), 2] + connection_all[k][i][2]

                    # if find no partA in the subset, create a new subset
                    elif not found and k < 17:
                        row = -1 * np.ones(20)
                        row[indexA] = partAs[i]
                        row[indexB] = partBs[i]
                        row[-1] = 2
                        row[-2] = sum(candidate[connection_all[k][i, :2].astype(int), 2]) + connection_all[k][i][2]
                        subset = np.vstack([subset, row])

        # -----------------------------------------------------
        # delete bad keypoint detection
        deleteIdx = [];
        for i in range(len(subset)):
            if subset[i][-1] < 4 or subset[i][-2] / subset[i][-1] < 0.4:
                deleteIdx.append(i)
        subset = np.delete(subset, deleteIdx, axis=0)

        # -----------------------------------------------------
        # visualize to render limbs of each person
        colors = [[255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0], [85, 255, 0], [0, 255, 0], \
                  [0, 255, 85], [0, 255, 170], [0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255], \
                  [170, 0, 255], [255, 0, 255], [255, 0, 170], [255, 0, 85]]

        stickwidth = 4
        canvas = oriImg.copy()
        for i in range(17):
            for n in range(len(subset)):  # each subset
                index = subset[n][np.array(limbSeq[i]) - 1]
                if -1 in index:
                    continue
                cur_canvas = canvas.copy()
                Y = candidate[index.astype(int), 0]
                X = candidate[index.astype(int), 1]
                mX = np.mean(X)
                mY = np.mean(Y)
                length = ((X[0] - X[1]) ** 2 + (Y[0] - Y[1]) ** 2) ** 0.5
                angle = math.degrees(math.atan2(X[0] - X[1], Y[0] - Y[1]))
                polygon = cv.ellipse2Poly((int(mY), int(mX)), (int(length / 2), stickwidth), int(angle), 0, 360, 1)
                cv.fillConvexPoly(cur_canvas, polygon, colors[i])
                canvas = cv.addWeighted(canvas, 0.4, cur_canvas, 0.6, 0)

        # plt.imshow(canvas[:, :, [2, 1, 0]])
        # fig = matplotlib.pyplot.gcf()
        # fig.set_size_inches(12, 12)
        cv.imwrite(render_image_path, canvas)

        all_keypoints = []
        print subset
        for i in range(0, len(subset)):
            keypoints = []
            for j in range(0, 18):
                index = subset[i][j].astype(int)
                if index == -1:
                    keypoints.append([0, 0, -1])
                    continue;
                X = candidate[index, 0]
                Y = candidate[index, 1]
                keypoints.append([X, Y, 1])
            print keypoints
            all_keypoints.append(keypoints)
        print len(all_keypoints)
        # -----------------------------------------------------
        # return center person keypoints
        centerIndex = self.getCenterKeypointsIndex(oriImg, all_keypoints)
        if centerIndex != -1:
            return all_keypoints[centerIndex]
        else:
            return []

    # return index of center person
    def getCenterKeypointsIndex(self, oriImg, keypoints_list):
        if len(keypoints_list) == 0:
            return -1
        elif len(keypoints_list) == 1:
            return 0

        height, width = oriImg.shape[0], oriImg.shape[1]
        center_index = 0
        center_dis = pow(height / 2, 2) + pow(width / 2, 2)

        for i in range(0, len(keypoints_list)):
            keypoints = keypoints_list[i]
            center = np.array([0.0, 0.0])
            count = 0
            for j in range(18):
                point = keypoints[j]
                if -1 in point:
                    continue
                center[0] += point[0]
                center[1] += point[1]
                count += 1
            center = center / count
            if (pow(center[0] - width / 2, 2) + pow(center[1] - height / 2, 2) < center_dis):
                center_dis = pow(center[0] - width / 2, 2) + pow(center[1] - height / 2, 2)
                center_index = i

        return center_index
        pass

    # return kind
    # 1.right hand 2.one hands vertical 3.left hands 4. two hands
    def getPoseKind(self, center_keypoints):
        if len(center_keypoints) == 0:
            return -1
        # left hand
        Lelbow = np.array(center_keypoints[6]).astype(float)
        Lwrist = np.array(center_keypoints[7]).astype(float)
        # right hand
        Relbow = np.array(center_keypoints[3]).astype(float)
        Rwrist = np.array(center_keypoints[4]).astype(float)
        print Lelbow, Lwrist

        if ((Lelbow[2] == -1 or Lwrist[2] == -1) and
                (Relbow[2] == -1 or Rwrist[2] == -1)):
            return -1
        elif ((Lelbow[2] == -1 or Lwrist[2] == -1)):
            if ((Rwrist[0] < Relbow[0] and Rwrist[1] <= Relbow[1])):
                # (Rwrist[0] < Relbow[0] and Rwrist[1] >= Relbow[1])):
                tanh = abs(Relbow[1] - Rwrist[1]) / (Relbow[0] - Rwrist[0])
                if tanh < 1.7:  # around 30
                    return 1  # right hand rise
                else:
                    return 2  # right hand vertical
            elif ((Rwrist[0] == Relbow[0] and Rwrist[1] <= Relbow[1])):
                return 2  # right hand vertical
        elif ((Relbow[2] == -1 or Rwrist[2] == -1)):
            if ((Lwrist[0] > Lelbow[0] and Lwrist[1] <= Lelbow[1])):
                # (Lwrist[0] < Lelbow[0] and Lwrist[1] >= Lelbow[1])):
                tanh = abs(Lelbow[1] - Lwrist[1]) / (Lwrist[0] - Lelbow[0])
                if tanh < 1.7:  # around 60
                    return 3  # left hand rise
                else:  # larger 60
                    return 4  # left hand vertical
            elif (Lwrist[0] == Lelbow[0] and Lwrist[1] <= Lelbow[1]):
                return 2
        else:
            tanhR = -1
            tanhL = -1
            if ((Rwrist[0] == Relbow[0] and Rwrist[1] <= Relbow[1])):
                tanhR = 10
            elif ((Rwrist[0] < Relbow[0] and Rwrist[1] <= Relbow[1])):
                # (Rwrist[0] < Relbow[0] and Rwrist[1] >= Relbow[1])):
                tanhR = abs(Relbow[1] - Rwrist[1]) / (Relbow[0] - Rwrist[0])

            if ((Lwrist[0] == Lelbow[0] and Lwrist[1] <= Lelbow[1])):
                tanhL = 10
            elif ((Lwrist[0] > Lelbow[0] and Lwrist[1] <= Lelbow[1])):
                # (Rwrist[0] < Relbow[0] and Rwrist[1] >= Relbow[1])):
                tanhL = abs(Lelbow[1] - Lwrist[1]) / (Lwrist[0] - Lelbow[0])
            print tanhR, tanhL
            if (tanhR == -1 and tanhL == -1):
                return -1  # two hand up
            elif (tanhR == -1):
                if tanhL < 1.7:
                    return 3
                else:
                    return 4
            elif (tanhL == -1):
                if tanhR < 1.7:
                    return 1
                else:
                    return 2
            else:
                if tanhR > 1.7 and tanhL > 1.7:
                    return 6
                else:
                    return 5
        return -1

    def setResultImage(self, filepath):
        self.resultImagePath = filepath

    def getResultImage(self):
        return self.resultImagePath


if __name__ == "__main__":
    #init model
    param, model = config_reader()

    # multiplier = [x * model['boxsize'] / oriImg.shape[0] for x in param['scale_search']]
    if param['use_gpu']:
        caffe.set_mode_gpu()
        caffe.set_device(param['GPUdeviceNumber'])  # set to your device!
    else:
        caffe.set_mode_cpu()
    net = caffe.Net(model['deployFile'], model['caffemodel'], caffe.TEST)
    image = cv.imread('../sample_image/8.jpeg')
    obj = PoseEstimation()
    centerHumanKeypoint = obj.KeypointDetection('../sample_image/9.jpeg', '../sample_image/result.jpg')
    poseKind = obj.getPoseKind(centerHumanKeypoint)
    print "poseKind:", poseKind
    kindName = ['left hand rise up', 'left hand rise vertically',
                'right hand rise up', 'right hand rise vertically',
                'two hands rise up', 'two hands rise vertically']
    if poseKind != -1:
        print 'Pose kind: ', kindName[poseKind - 1]
    else:
        print 'No defined Pose'
    pass
