
import os
import numpy as np
import h5py
from .base_regre import base_regre
from utils.iso_boxes import iso_cube


class base_detec(base_regre):
    """ basic detection based method
    """
    def __init__(self, args):
        super(base_detec, self).__init__(args)
        self.num_appen = 4

    def receive_data(self, thedata, args):
        """ Receive parameters specific to the data """
        super(base_detec, self).receive_data(thedata, args)
        self.provider_worker = args.data_provider.prow_heatmap
        self.yanker = self.provider.yank_heatmap

    def draw_random(self, thedata, args):
        import matplotlib.pyplot as mpplot
        from cv2 import resize as cv2resize

        with h5py.File(self.appen_train, 'r') as h5file:
            store_size = h5file['index'].shape[0]
            frame_id = np.random.choice(store_size)
            img_id = h5file['index'][frame_id, 0]
            frame_h5 = np.squeeze(h5file['frame'][frame_id, ...], -1)
            poses_h5 = h5file['poses'][frame_id, ...].reshape(-1, 3)
            resce_h5 = h5file['resce'][frame_id, ...]

        print('[{}] drawing image #{:d} ...'.format(self.name_desc, img_id))
        print(np.min(frame_h5), np.max(frame_h5))
        print(np.histogram(frame_h5, range=(1e-4, np.max(frame_h5))))
        print(np.min(poses_h5, axis=0), np.max(poses_h5, axis=0))
        from colour import Color
        colors = [Color('orange').rgb, Color('red').rgb, Color('lime').rgb]
        mpplot.subplots(nrows=2, ncols=2, figsize=(2 * 5, 2 * 5))

        ax = mpplot.subplot(2, 2, 3)
        mpplot.gca().set_title('test storage read')
        resce3 = resce_h5[0:4]
        cube = iso_cube()
        cube.load(resce3)
        # need to maintain both image and poses at the same scale
        sizel = np.floor(resce3[0]).astype(int)
        ax.imshow(
            cv2resize(frame_h5, (sizel, sizel)),
            cmap='bone')
        pose3d = cube.trans_scale_to(poses_h5)
        pose2d, _ = cube.project_pca(pose3d, roll=0, sort=False)
        pose2d *= sizel
        args.data_draw.draw_pose2d(
            thedata,
            pose2d,
        )

        ax = mpplot.subplot(2, 2, 4)
        mpplot.gca().set_title('test output')
        img_name = args.data_io.index2imagename(img_id)
        img = args.data_io.read_image(os.path.join(self.image_dir, img_name))
        ax.imshow(img, cmap='bone')
        pose_raw = self.yanker(poses_h5, resce_h5, self.caminfo)
        args.data_draw.draw_pose2d(
            thedata,
            args.data_ops.raw_to_2d(pose_raw, thedata)
        )
        rects = cube.proj_rects_3(
            args.data_ops.raw_to_2d, self.caminfo
        )
        for ii, rect in enumerate(rects):
            rect.draw(colors[ii])

        ax = mpplot.subplot(2, 2, 1)
        mpplot.gca().set_title('test input')
        annot_line = args.data_io.get_line(
            thedata.training_annot_cleaned, img_id)
        img_name, pose_raw = args.data_io.parse_line_annot(annot_line)
        img = args.data_io.read_image(os.path.join(self.image_dir, img_name))
        ax.imshow(img, cmap='bone')
        args.data_draw.draw_pose2d(
            thedata,
            args.data_ops.raw_to_2d(pose_raw, thedata))

        ax = mpplot.subplot(2, 2, 2)
        mpplot.gca().set_title('test storage write')
        img_name, frame, poses, resce = self.provider_worker(
            annot_line, self.image_dir, thedata)
        frame = np.squeeze(frame, axis=-1)
        poses = poses.reshape(-1, 3)
        if (
                (1e-4 < np.linalg.norm(frame_h5 - frame)) or
                (1e-4 < np.linalg.norm(poses_h5 - poses))
        ):
            print(np.linalg.norm(frame_h5 - frame))
            print(np.linalg.norm(poses_h5 - poses))
            print('ERROR - h5 storage corrupted!')
        resce3 = resce[0:4]
        cube = iso_cube()
        cube.load(resce3)
        sizel = np.floor(resce3[0]).astype(int)
        ax.imshow(
            cv2resize(frame, (sizel, sizel)),
            cmap='bone')
        pose3d = cube.trans_scale_to(poses)
        pose2d, _ = cube.project_pca(pose3d, roll=0, sort=False)
        pose2d *= sizel
        args.data_draw.draw_pose2d(
            thedata,
            pose2d,
        )

        mpplot.savefig(os.path.join(
            args.predict_dir,
            'draw_{}.png'.format(self.name_desc)))
        if self.args.show_draw:
            mpplot.show()
        print('[{}] drawing image #{:d} - done.'.format(
            self.name_desc, img_id))
